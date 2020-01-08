# -*- coding: utf-8 -*-
'''
Contains all the necessary functions to convert a PAR
Header (and corresponding REC image) to nifti in
BIDS format (by default).
'''
# 
# 
# -*- coding: utf-8 -*-
# title           : convertSourcePAR.py
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2019 08 14 19:30:18
# version         : 0.0.1
# usage           : convertSourcePAR.py [-h,--help]
# notes           : [notes]
# python_version  : 3.7.3
# ==============================================================================

# Import Modules

import os
import shutil
import glob
import subprocess
import random
import re
import json
import pandas as pd
import nibabel as nib
from scipy import stats

# Random integer max range value
n = 10000


def rename_par_rec_dir(raw_data_dir):
    '''
    DEPRICATED: This function should not be used. As many problems 
        are caused, on only one or several parts of the filename are 
        changed. One should just put the file name in quotes.

    Renames The PAR REC raw data directory such that
    the spaces in PAR REC are replaced with an underscore.
    ---
    Input:
    - Raw Data PAR REC directory.
    ---
    Returns: 
    - Renamed PAR_REC directory with an underscore.
    '''
    if "PAR REC" in raw_data_dir:
        new_dir = os.path.join(os.path.dirname(raw_data_dir), "PAR_REC")
        os.rename(raw_data_dir, new_dir)
    else:
        new_dir = raw_data_dir
    new_dir = os.path.abspath(new_dir)
    return (new_dir)


def get_num_frames(nii_file):
    '''Gets the number of frames for a DW or fMR image series.'''

    img = nib.load(nii_file)
    frames = img.header.get_data_shape()
    num_frames = frames[3]

    # num_frames = subprocess.check_output(["fslval", nii_file, "dim4"])
    num_frames = str(num_frames)
    num_frames = int(re.sub('[^0-9]', '', num_frames))  # Strip non-numeric information
    return (num_frames)


def get_epi_factor(par_file):
    '''
    Gets EPI factor (Echo Train Length) from Philips' PAR/XML Header.
    This uses the RegEx '.    EPI factor        <0,1=no EPI>     : '
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    regexp = re.compile(r'.    EPI factor        <0,1=no EPI>     :   .*?([0-9.-]+)')  # Search string for RegEx
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                epi_factor = match.group(1)
                epi_factor = int(epi_factor)
    return (epi_factor)


def get_wfs(par_file):
    '''
    Gets Water Fat Shift from Philips' PAR/XML Header.
    This uses the RegEx '.    Water Fat shift \[pixels\]           :   '
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    regexp = re.compile(
        r'.    Water Fat shift \[pixels\]           :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                wfs = match.group(1)
                wfs = float(wfs)
    return (wfs)


def get_bval(par_file):
    '''
    Extracts bvalue from PAR/XML REC Header.
    This assumes a single shell acquisition,
    not a multi-shell acquisition.
    Default is 0.
    '''
    bvalue = 0
    bval_df = pd.read_csv(par_file, sep="\s+", skiprows=98,
                         low_memory=False)  # Skip the first 99 rows as this is extraneous information
    arr = bval_df['echo'].values  # All the b-values are listed under 'echo' using this method.
    mode_arr = stats.mode(arr, nan_policy='omit')  # Obtain the mode (most frequent number)
    bvalue = int(re.sub('[^0-9]', '', str(mode_arr[0])))

    return (bvalue)


def get_acc(par_file):
    '''Acceleration (SENSE) factor for Scanner. Default is 1.'''
    acc = 1
    regexp = re.compile(r' SENSE *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                acc = match.group(1)
                acc = float(acc)
    return (acc)


def get_mb(par_file):
    '''Multi-Band factor for Scanner. Default is 1.'''
    mb = 1
    regexp = re.compile(r' MB *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                mb = match.group(1)
                mb = int(mb)
    return (mb)


def update_json(json_file, bvalue='unknown', wfs='unknown', epi_factor='unknown', acc=1, mb=1, scan_time='unknown', task_name=""):
    '''
    Appends additional information not normally included in the JSON file side car
    as dcm2niix does not normally look for these in PAR/XML REC headers.
    '''

    # "epi_factor":epi_factor changed to "EchoTrainLength":epi_factor
    # for easier JSON parsing.

    if task_name == "":
        # In the case of empty task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time,
            "SourceDataFormat": "PAR_REC"}
    else:
        # In the case of populated task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time, "TaskName": task_name,
            "SourceDataFormat": "PAR_REC"}

    with open(json_file, "r") as read_file:
        data2 = json.load(read_file)

    data2.update(data)

    with open(json_file, 'w+') as outfile:
        json.dump(data2, outfile, indent=4)

    return (json_file)


def get_num_runs(out_dir, task="", acq="", dirs="", bval="", scan=""):
    '''
    Determines run number of a scan (e.g. T1w, T2w, bold, dwi etc.)
    in an output directory by globbing the directory for the number
    of compressed niftis of the same scan.
    '''

    runs = os.path.join(out_dir, f"*{task}*{acq}*{dirs}*{bval}*{scan}*.nii*")
    run_num = len(glob.glob(runs))
    run_num = run_num + 1

    return (run_num)


def scan_tech(par_file):
    '''
    Parses PAR/XML REC header for sequence/technique
    used to obtain the image (if not mentioned in the
    filename). The RegEx strings that are searched are
    protocol names specific to CCHMC scanners.
    '''
    regexp = re.compile(r'.    Technique                          :  .*', re.M | re.I)
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scan_id = match.group()
    if 'T1' in scan_id or 'TFE' in scan_id:
        scan = 'T1'
    elif 'T2' in scan_id or 'TSE' in scan_id:
        scan = 'T2'
    elif 'DwiSE' in scan_id:
        scan = 'dwi'
    elif 'FEEPI' in scan_id:
        scan = 'func'
    else:
        scan = 'unknown_scan'

    return (scan)


def get_scan_time(par_file):
    '''
    Gets Water Fat Shift from Philips' PAR/XML Header.
    This uses the RegEx 'Scan Duration [sec]' string
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    scan_time = 'unknown'
    regexp = re.compile(
        r'.    Scan Duration \[sec\]                :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scan_time = match.group(1)
                scan_time = float(scan_time)
    return (scan_time)


def get_echo(json_file):
    '''
    Gets the echo time (TE) from a 
    JSON sidecar file for an acquisition.
    '''
    with open(json_file, "r") as read_file:
        data = json.load(read_file)

    echo = data.get("EchoTime")

    return (echo)


def convert_par_file(par_file, out_dir, basename):
    '''
    Converts PAR/XML REC File to NifTI.
    This works best using a temporary directory
    as globbing is used to find the output files
    for the return.
    '''
    # make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{par_file}"])

    # Get filenames
    dir_path = os.path.join(out_dir, basename)
    nii_file = glob.glob(dir_path + '*.nii*')
    json_file = glob.glob(dir_path + '*.json')

    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)

    return (nii_file, json_file)


def convert_par_dwi(par_file, out_dir, basename):
    '''
    Converts PAR/XML REC File to DWI NifTI.
    This works best using a temporary directory
    as globbing is used to find the output files
    for the return.
    '''
    # make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{par_file}"])

    # Get filenames
    dir_path = os.path.join(out_dir, basename)
    nii_file = glob.glob(dir_path + '*.nii*')
    json_file = glob.glob(dir_path + '*.json')
    bval = glob.glob(dir_path + '*.bval')
    bvec = glob.glob(dir_path + '*.bvec')

    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)
    bval = ''.join(bval)
    bvec = ''.join(bvec)

    return (nii_file, json_file, bval, bvec)


def convert_par_fmap(par_file, out_dir, basename):
    '''
    Converts PAR/XML REC File to DWI NifTI.
    This works best using a temporary directory
    as globbing is used to find the output files
    for the return.
    '''
    # make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{par_file}"])

    # Get filenames
    dir_path = os.path.join(out_dir, basename)
    nii_real = glob.glob(dir_path + '*real*.nii*')
    json_real = glob.glob(dir_path + '*real*.json')
    nii_mag = glob.glob(dir_path + '.nii*')
    json_mag = glob.glob(dir_path + '.json')

    # Convert lists to strings
    nii_real = ''.join(nii_real)
    json_real = ''.join(json_real)
    nii_mag = ''.join(nii_mag)
    json_mag = ''.join(json_mag)

    return (nii_real, json_real, nii_mag, json_mag)


def data_to_bids_anat(out_dir, par_file, sub, scan, ses=1, scan_type='anat'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outdir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

    # Make output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [nii_file, json_file] = convert_par_file(par_file, tmp_out_dir, tmp_basename)

    nii_file = os.path.abspath(nii_file)
    json_file = os.path.abspath(json_file)

    # Append w to T1/T2 if not already done
    if scan in 'T1' or scan in 'T2':
        scan = scan + 'w'
    else:
        scan = scan

    # Get Run number
    run = get_num_runs(outdir, scan=scan)
    run = '{:02}'.format(run)

    # Additional sequence/modality parameters
    epi_factor = get_epi_factor(par_file)
    wfs = get_wfs(par_file)
    bval = get_bval(par_file)
    acc = get_acc(par_file)
    mb = get_mb(par_file)
    sct = get_scan_time(par_file)

    # update JSON file with additional parameters
    json_file = update_json(json_file, bval, wfs, epi_factor, acc, mb, sct)

    # Create output filenames
    out_name = f"sub-{sub}_ses-{ses}_run-{run}_{scan}"
    out_nii = os.path.join(outdir, out_name + '.nii.gz')
    out_json = os.path.join(outdir, out_name + '.json')

    os.rename(nii_file, out_nii)
    os.rename(json_file, out_json)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_func(out_dir, par_file, sub, ses=1, scan_type='func', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outdir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

    # Make output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [nii_file, json_file] = convert_par_file(par_file, tmp_out_dir, tmp_basename)

    nii_file = os.path.abspath(nii_file)
    json_file = os.path.abspath(json_file)

    # Decide if file is 4D timeseries or single-band reference
    num_frames = get_num_frames(nii_file)
    if num_frames == 1:
        acq = 'AP'
        run = get_num_runs(outdir, scan='sbref', acq=acq, task=task)
        run = '{:02}'.format(run)
        out_name = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_sbref"
    else:
        run = get_num_runs(outdir, scan='bold', acq=acq, task=task)
        run = '{:02}'.format(run)
        out_name = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_bold"

    # Additional sequence/modality parameters
    epi_factor = get_epi_factor(par_file)
    wfs = get_wfs(par_file)
    bval = get_bval(par_file)
    acc = get_acc(par_file)
    mb = get_mb(par_file)
    sct = get_scan_time(par_file)

    # update JSON file with additional parameters
    json_file = update_json(json_file, bval, wfs, epi_factor, acc, mb, sct)

    # Create output filenames
    out_nii = os.path.join(outdir, out_name + '.nii.gz')
    out_json = os.path.join(outdir, out_name + '.json')

    os.rename(nii_file, out_nii)
    os.rename(json_file, out_json)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_fmap(out_dir, par_file, sub, ses=1, scan_type='fmap', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outdir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

    # Make output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [nii_real, json_real, nii_mag, json_mag] = convert_par_fmap(par_file, tmp_out_dir, tmp_basename)

    nii_real = os.path.abspath(nii_real)
    json_real = os.path.abspath(json_real)
    nii_mag = os.path.abspath(nii_mag)
    json_mag = os.path.abspath(json_mag)

    # Additional sequence/modality parameters
    epi_factor = get_epi_factor(par_file)
    wfs = get_wfs(par_file)
    bval = get_bval(par_file)
    acc = get_acc(par_file)
    mb = get_mb(par_file)
    sct = get_scan_time(par_file)

    # update JSON file with additional parameters
    json_real = update_json(json_real, bval, wfs, epi_factor, acc, mb, sct)
    json_mag = update_json(json_mag, bval, wfs, epi_factor, acc, mb, sct)

    # Get run number
    run = get_num_runs(outdir, scan='magnitude', acq=acq, task=task)
    run = '{:02}'.format(run)

    # Create output names
    out_real = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_fieldmap"
    out_mag = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_magnitude"

    out_real_nii = os.path.join(outdir, out_real + '.nii.gz')
    out_mag_nii = os.path.join(outdir, out_mag + '.nii.gz')

    out_real_json = os.path.join(outdir, out_real + '.json')
    out_mag_json = os.path.join(outdir, out_mag + '.json')

    os.rename(nii_real, out_real_nii)
    os.rename(nii_mag, out_mag_nii)

    os.rename(json_real, out_real_json)
    os.rename(json_mag, out_mag_json)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_dwi(out_dir, par_file, sub, ses=1, scan_type='dwi', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outdir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

    # Make output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Additional sequence/modality parameters
    epi_factor = get_epi_factor(par_file)
    wfs = get_wfs(par_file)
    bval = get_bval(par_file)
    acc = get_acc(par_file)
    mb = get_mb(par_file)
    sct = get_scan_time(par_file)

    # IF statement to handle either a B0 or b > 0 acquisition.
    if bval == 0:
        # Convert PAR file
        [nii_file, json_file] = convert_par_file(par_file, tmp_out_dir, tmp_basename)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)

        # Hard-coded to differentiate between the 
        # different echo B0s of the b800 or b2000
        # acquisitions.
        echo = get_echo(json_file)
        if echo < 0.093:
            dirs = 6
        else:
            dirs = 7
        dirs = '{:03}'.format(dirs)

        # update JSON file with additional parameters
        json_file = update_json(json_file, bval, wfs, epi_factor, acc, mb, sct)

        # Get Run Number
        acq = 'AP'
        run = get_num_runs(outdir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
        run = '{:02}'.format(run)
        out_name = f"sub-{sub}_ses-{ses}_dir-{acq}_acq-{dirs}dirs_bval-b{bval}_run-{run}_dwi"

        # Create output filenames
        out_nii = os.path.join(outdir, out_name + '.nii.gz')
        out_json = os.path.join(outdir, out_name + '.json')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)
    else:
        # Convert PAR file
        [nii_file, json_file, bvals, bvecs] = convert_par_dwi(par_file, tmp_out_dir, tmp_basename)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)
        bvals = os.path.abspath(bvals)
        bvecs = os.path.abspath(bvecs)

        # Number of directions for CCHMC diffusion protocol correspond
        # to the number of frames in the 4D nifti file.
        # This information can also be obtained from the PAR/XML REC Header
        dirs = get_num_frames(nii_file)
        dirs = '{:03}'.format(dirs)

        # update JSON file with additional parameters
        json_file = update_json(json_file, bval, wfs, epi_factor, acc, mb, sct)

        # Get Run Number
        run = get_num_runs(outdir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
        run = '{:02}'.format(run)
        out_name = f"sub-{sub}_ses-{ses}_dir-{acq}_acq-{dirs}dirs_bval-b{bval}_run-{run}_dwi"

        # Create output filenames
        out_nii = os.path.join(outdir, out_name + '.nii.gz')
        out_json = os.path.join(outdir, out_name + '.json')
        out_bvals = os.path.join(outdir, out_name + '.bval')
        out_bvecs = os.path.join(outdir, out_name + '.bvec')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)
        os.rename(bvals, out_bvals)
        os.rename(bvecs, out_bvecs)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_unknown(out_dir, par_file, sub, ses=1):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Get Acquisition Technique from PAR/REC
    # Header.
    scan = scan_tech(par_file)

    # Convert PAR file
    if 'T1' in scan:
        try:
            data_to_bids_anat(out_dir, par_file, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'T2' in scan:
        try:
            data_to_bids_anat(out_dir, par_file, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'func' in scan:
        try:
            data_to_bids_func(out_dir, par_file, sub, ses=ses)
        except UnboundLocalError:
            pass
    elif 'dwi' in scan:
        try:
            data_to_bids_dwi(out_dir, par_file, sub, ses=ses)
        except UnboundLocalError:
            pass
    else:
        try:
            data_to_bids_anat(out_dir, par_file, sub, scan='unknown_scan', scan_type='unknown', ses=ses)
        except UnboundLocalError:
            pass
