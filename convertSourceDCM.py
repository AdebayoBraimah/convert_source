# -*- coding: utf-8 -*-
'''
Contains all the necessary functions to convert
dicom images to nifti in
BIDS format (by default).
'''
# 
# 
# -*- coding: utf-8 -*-
# title           : convertSourceDCM.py
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2019 08 15 16:19:38
# version         : 0.0.x
# usage           : convertSourceDCM.py [-h,--help]
# notes           : [notes]
# python_version  : 3.7.3
# ==============================================================================

# Import Modules

import pydicom
import json
import re
import os
import shutil
import glob
import random
import subprocess
import nibabel as nib

# Random integer max range value
n = 10000


def get_bval(dcm_dir):
    '''
    Extracts b-value from file description
    in the DICOM header.
    Assumes single shell acquisition.
    Input is either dicom file or 
    dicom directory.
    '''
    # Initialize bval to 0
    bval = 0

    # Load dicom data
    ds = pydicom.dcmread(dcm_dir)

    # Get image descriptor
    line = ds.SeriesDescription
    match1 = re.search(r' B.*?([0-9.-]+)', line, re.M | re.I)
    match2 = re.search(r' b.*?([0-9.-]+)', line, re.M | re.I)
    if match1:
        bval = match1.group(0)
        bval = int(re.sub('[^0-9]', '', bval))
    elif match2:
        bval = match2.group(0)
        bval = int(re.sub('[^0-9]', '', bval))

    return (bval)


def get_acc(dcm_dir):
    '''
    Extracts Acceleration (SENSE) Factor 
    from file description in the DICOM 
    header for philips MR scanners.
    Input is either dicom file or 
    dicom directory.
    '''

    # Initialize acc to 1
    acc = 1

    # Load dicom data
    ds = pydicom.dcmread(dcm_dir)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'SENSE .*?([0-9.-]+)', line, re.M | re.I)
    if match:
        acc = match.group(1)
        acc = float(acc)

    return (acc)


def get_mb(dcm_dir):
    '''
    Extracts Multi-Band Factor 
    from file description in the DICOM 
    header for philips MR scanners.
    Input is either dicom file or 
    dicom directory.
    '''

    # Initialize acc to 1
    mb = 1

    # Load dicom data
    ds = pydicom.dcmread(dcm_dir)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'MB.*?([0-9.-]+)', line, re.M | re.I)
    if match:
        mb = match.group(1)
        mb = int(mb)

    return (mb)


def get_scan_time(dcm_dir):
    '''
    Gets the scan time (s) from
    dicom data.
    '''

    # Load data
    ds = pydicom.dcmread(dcm_dir)

    # Gets scan time
    try:
        scan_time = ds.AcquisitionDuration
    except AttributeError:
        pass
        scan_time = 'unknown'

    return (scan_time)


def update_json(json_file, bvalue='unknown', acc=1, mb=1, scan_time='unknown', task_name=""):
    '''
    Updates JSON sidecar file
    for an associated nifti file.
    The following information is 
    added to the JSON sidecar:
    - Acceleration (SENSE) Factor
    - Multi-Band Factor
    - b-value(s)
    - scan time (s)
    '''

    if task_name == "":
        # In the case of empty task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time,
            "SourceDataFormat": "DICOM"}
    else:
        # In the case of populated task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time, "TaskName": task_name,
            "SourceDataFormat": "DICOM"}

    with open(json_file, "r") as read_file:
        data2 = json.load(read_file)

    data2.update(data)

    with open(json_file, 'w+') as out_file:
        json.dump(data2, out_file, indent=4)

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

def get_num_frames(nii_file):
    '''Gets the number of frames for a DW or fMR image series.'''

    img = nib.load(nii_file)
    frames = img.header.get_data_shape()
    num_frames = frames[3]

    # num_frames = subprocess.check_output(["fslval", nii_file, "dim4"])
    num_frames = str(num_frames)
    num_frames = int(re.sub('[^0-9]', '', num_frames))  # Strip non-numeric information
    return (num_frames)


def get_scan_name(dcm_dir):
    '''
    Extracts scan name/type 
    from file description in the DICOM 
    header for philips MR scanners.
    Input is either dicom file or 
    dicom directory.
    '''

    # Load dicom data
    ds = pydicom.dcmread(dcm_dir)

    # Get image descriptor
    scan_id = ds.SeriesDescription
    # match = re.search(r'SENSE .*?([0-9.-]+)', line, re.M|re.I)
    if 'T1' in scan_id or 'TFE' in scan_id:
        scan = 'T1'
    elif 'T2' in scan_id or 'TSE' in scan_id:
        scan = 'T2'
    elif 'DwiSE' in scan_id or 'DTI' in scan_id or 'dti' in scan_id or 'DWI' in scan_id:
        scan = 'dwi'
    elif 'FEEPI' in scan_id or 'fMR' in scan_id:
        scan = 'func'
    else:
        scan = 'unknown_scan'

    return (scan)


def get_echo(json_file):
    '''
    Gets the echo time (TE) from a 
    JSON sidecar file for an acquisition.
    '''
    with open(json_file, "r") as read_file:
        data = json.load(read_file)

    echo = data.get("EchoTime")

    return (echo)


def convert_dcm(dcm, out_dir, basename):
    '''
    Converts dicom to nifti.
    Expects dicom file or directory
    as input.
    '''

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{dcm}"])

    # remove extra DWI file (in the case of B0)
    dir_path = os.path.join(out_dir, basename)
    adc_nii = glob.glob(dir_path + '*ADC*.nii*')
    adc_nii = ''.join(adc_nii)
    if os.path.isfile(adc_nii):
        os.remove(adc_nii)

    # Get filenames
    dir_path = os.path.join(out_dir, basename)
    nii_file = glob.glob(dir_path + '*.nii*')
    json_file = glob.glob(dir_path + '*.json')

    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)

    return (nii_file, json_file)


def convert_dcm_dwi(dcm, out_dir, basename):
    '''
    Converts DICOM File to DWI NifTI.
    This works best using a temporary directory
    as globbing is used to find the output files
    for the return.
    '''
    # make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{dcm}"])

    # remove extra DWI file
    dir_path = os.path.join(out_dir, basename)
    adc_nii = glob.glob(dir_path + '*ADC*.nii*')
    adc_nii = ''.join(adc_nii)
    if os.path.isfile(adc_nii):
        os.remove(adc_nii)

    # Get filenames
    nii_file = glob.glob(dir_path + '.nii*')
    json_file = glob.glob(dir_path + '.json')
    bval = glob.glob(dir_path + '*.bval')
    bvec = glob.glob(dir_path + '*.bvec')

    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)
    bval = ''.join(bval)
    bvec = ''.join(bvec)

    return (nii_file, json_file, bval, bvec)


def convert_dcm_fmap(dcm, out_dir, basename):
    '''
    Converts DICOM File to NifTI.
    This works best using a temporary directory
    as globbing is used to find the output files
    for the return.
    '''
    # make output directory
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Convert the data
    subprocess.call(["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{dcm}"])

    # Get filenames
    dir_path = os.path.join(out_dir, basename)
    nii_real = glob.glob(dir_path + '*e1.nii*')
    json_real = glob.glob(dir_path + '*e1.json')
    nii_mag = glob.glob(dir_path + '*e1a.nii*')
    json_mag = glob.glob(dir_path + '*e1a.json')

    # Convert lists to strings
    nii_real = ''.join(nii_real)
    json_real = ''.join(json_real)
    nii_mag = ''.join(nii_mag)
    json_mag = ''.join(json_mag)

    return (nii_real, json_real, nii_mag, json_mag)


def data_to_bids_anat(out_dir, dcm, sub, scan, ses=1, scan_type='anat'):
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

    # Convert DCM file
    [nii_file, json_file] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

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
    bval = get_bval(dcm)
    acc = get_acc(dcm)
    mb = get_mb(dcm)
    sct = get_scan_time(dcm)

    # update JSON file with additional parameters
    json_file = update_json(json_file, bval, acc, mb, sct)

    # Create output filenames
    out_name = f"sub-{sub}_ses-{ses}_run-{run}_{scan}"
    out_nii = os.path.join(outdir, out_name + '.nii.gz')
    out_json = os.path.join(outdir, out_name + '.json')

    os.rename(nii_file, out_nii)
    os.rename(json_file, out_json)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_func(out_dir, dcm, sub, ses=1, scan_type='func', task='rest', acq='PA'):
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

    # Convert DCM file
    [nii_file, json_file] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

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
    bval = get_bval(dcm)
    acc = get_acc(dcm)
    mb = get_mb(dcm)
    sct = get_scan_time(dcm)

    # update JSON file with additional parameters
    json_file = update_json(json_file, bval, acc, mb, sct)

    # Create output filenames
    out_nii = os.path.join(outdir, out_name + '.nii.gz')
    out_json = os.path.join(outdir, out_name + '.json')

    os.rename(nii_file, out_nii)
    os.rename(json_file, out_json)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_fmap(out_dir, dcm, sub, ses=1, scan_type='fmap', task='rest', acq='PA'):
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

    # Convert DCM file
    [nii_real, json_real, nii_mag, json_mag] = convert_dcm_fmap(dcm, tmp_out_dir, tmp_basename)

    nii_real = os.path.abspath(nii_real)
    json_real = os.path.abspath(json_real)
    nii_mag = os.path.abspath(nii_mag)
    json_mag = os.path.abspath(json_mag)

    # Additional sequence/modality parameters
    bval = get_bval(dcm)
    acc = get_acc(dcm)
    mb = get_mb(dcm)
    sct = get_scan_time(dcm)

    # update JSON file with additional parameters
    json_real = update_json(json_real, bval, acc, mb, sct)
    json_mag = update_json(json_mag, bval, acc, mb, sct)

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


def data_to_bids_dwi(out_dir, dcm, sub, ses=1, scan_type='dwi', acq='PA'):
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
    bval = get_bval(dcm)
    acc = get_acc(dcm)
    mb = get_mb(dcm)
    sct = get_scan_time(dcm)

    # IF statement to handle either a B0 or b > 0 acquisition.
    if bval == 0:
        # Convert dcm file
        [nii_file, json_file] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

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
        json_file = update_json(json_file, bval, acc, mb, sct)

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
        # Convert dcm file
        [nii_file, json_file, bvals, bvecs] = convert_dcm_dwi(dcm, tmp_out_dir, tmp_basename)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)
        bvals = os.path.abspath(bvals)
        bvecs = os.path.abspath(bvecs)

        # Number of directions for CCHMC diffusion protocol correspond
        # to the number of frames in the 4D nifti file.
        dirs = get_num_frames(nii_file)
        dirs = '{:03}'.format(dirs)

        # update JSON file with additional parameters
        json_file = update_json(json_file, bval, acc, mb, sct)

        # Get Run Number
        run = get_num_runs(outdir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
        run = '{:02}'.format(run)
        out_name = f"sub-{sub}_ses-{ses}_dir-{acq}_acq-{dirs}dirs_bval-b{bval}_run-{run}_dwi"

        # Create output filenames
        out_nii = os.path.join(outdir, out_name + '.nii.gz')
        out_json = os.path.join(outdir, out_name + '.json')
        outBvals = os.path.join(outdir, out_name + '.bval')
        outBvecs = os.path.join(outdir, out_name + '.bvec')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)
        os.rename(bvals, outBvals)
        os.rename(bvecs, outBvecs)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data_to_bids_unknown(out_dir, dcm, sub, ses=1):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Get Acquisition Technique from dicom
    # Header.
    scan = get_scan_name(dcm)

    # Convert DCM file
    if 'T1' in scan:
        try:
            data_to_bids_anat(out_dir, dcm, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'T2' in scan:
        try:
            data_to_bids_anat(out_dir, dcm, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'func' in scan:
        try:
            data_to_bids_func(out_dir, dcm, sub, ses=ses)
        except UnboundLocalError:
            pass
    elif 'dwi' in scan:
        try:
            data_to_bids_dwi(out_dir, dcm, sub, ses=ses)
        except UnboundLocalError:
            pass
    else:
        try:
            data_to_bids_anat(out_dir, dcm, sub, scan='unknown_scan', scan_type='unknown', ses=ses)
        except UnboundLocalError:
            pass
