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
from scipy import stats

# Random integer max range value
n = 10000


def renamePAR_REC_Dir(rawDataDir):
    '''
    Renames The PAR REC raw data directory such that
    the spaces in PAR REC are replaced with an underscore.
    ---
    Input:
    - Raw Data PAR REC directory.
    ---
    Returns: 
    - Renamed PAR_REC directory with an underscore.
    '''
    if "PAR REC" in rawDataDir:
        newDir = os.path.join(os.path.dirname(rawDataDir), "PAR_REC")
        os.rename(rawDataDir, newDir)
    else:
        newDir = rawDataDir
    newDir = os.path.abspath(newDir)
    return (newDir)


def getNumFrames(niiFile):
    '''Gets the number of frames for a DW or fMR image series.'''

    numFrames = subprocess.check_output(["fslval", niiFile, "dim4"])
    numFrames = str(numFrames)
    numFrames = int(re.sub('[^0-9]', '', numFrames))  # Strip non-numeric information
    return (numFrames)


def getEPIfactor(parFile):
    '''
    Gets EPI factor from Philips' PAR/XML Header.
    This uses the RegEx '.    EPI factor        <0,1=no EPI>     : '
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    regexp = re.compile(r'.    EPI factor        <0,1=no EPI>     :   .*?([0-9.-]+)')  # Search string for RegEx
    with open(parFile) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                epiFactor = match.group(1)
                epiFactor = int(epiFactor)
    return (epiFactor)


def getWFS(parFile):
    '''
    Gets Water Fat Shift from Philips' PAR/XML Header.
    This uses the RegEx '.    Water Fat shift \[pixels\]           :   '
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    regexp = re.compile(
        r'.    Water Fat shift \[pixels\]           :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(parFile) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                wfs = match.group(1)
                wfs = float(wfs)
    return (wfs)


def getBval(parFile):
    '''
    Extracts bvalue from PAR/XML REC Header.
    This assumes a single shell acquisition,
    not a multi-shell acquisition.
    Default is 0.
    '''
    bvalue = 0
    bvalDF = pd.read_csv(parFile, sep="\s+", skiprows=98,
                         low_memory=False)  # Skip the first 99 rows as this is extraneous information
    arr = bvalDF['echo'].values  # All the b-values are listed under 'echo' using this method.
    modeArr = stats.mode(arr, nan_policy='omit')  # Obtain the mode (most frequent number)
    bvalue = int(re.sub('[^0-9]', '', str(modeArr[0])))

    return (bvalue)


def getAcc(parFile):
    '''Acceleration (SENSE) factor for Scanner. Default is 1.'''
    acc = 1
    regexp = re.compile(r' SENSE *?([0-9.-]+)')
    with open(parFile) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                acc = match.group(1)
                acc = float(acc)
    return (acc)


def getMB(parFile):
    '''Multi-Band factor for Scanner. Default is 1.'''
    mb = 1
    regexp = re.compile(r' MB *?([0-9.-]+)')
    with open(parFile) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                mb = match.group(1)
                mb = int(mb)
    return (mb)


def updateJSON(jsonFile, bvalue='unknown', wfs='unknown', epiFactor='unknown', acc=1, mb=1, scanTime='unknown', task_name=""):
    '''
    Appends additional information not normally included in the JSON file side car
    as dcm2niix does not normally look for these in PAR/XML REC headers.
    '''

    # "EPIFactor":epiFactor changed to "EchoTrainLength":epiFactor
    # for easier JSON parsing.

    if task_name == "":
        # In the case of empty task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epiFactor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "ScanTime": scanTime,
            "SourceDataFormat": "PAR_REC"}
    else:
        # In the case of populated task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epiFactor,
            "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "ScanTime": scanTime, "TaskName": task_name,
            "SourceDataFormat": "PAR_REC"}

    # data = {"WaterFatShift": wfs, "EchoTrainLength": epiFactor,
    #         "AccelerationFactor": acc, "MultibandAccelerationFactor": mb,
    #         "bvalue": bvalue, "ScanTime": scanTime,
    #         "SourceDataFormat": "PAR_REC"}

    with open(jsonFile, "r") as read_file:
        data2 = json.load(read_file)

    data2.update(data)

    with open(jsonFile, 'w+') as outfile:
        json.dump(data2, outfile, indent=4)

    return (jsonFile)


def getNumRuns(out_dir, task="", acq="", dirs="", bval="", scan=""):
    '''
    Determines run number of a scan (e.g. T1w, T2w, bold, dwi etc.)
    in an output directory by globbing the directory for the number
    of compressed niftis of the same scan.
    '''

    runs = os.path.join(out_dir, f"*{task}*{acq}*{dirs}*{bval}*{scan}*.nii*")
    runNum = len(glob.glob(runs))
    runNum = runNum + 1

    return (runNum)


def scanTech(parFile):
    '''
    Parses PAR/XML REC header for sequence/technique
    used to obtain the image (if not mentioned in the
    filename). The RegEx strings that are searched are
    protocol names specific to CCHMC scanners.
    '''
    regexp = re.compile(r'.    Technique                          :  .*', re.M | re.I)
    with open(parFile) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scanID = match.group()
    if 'T1' in scanID or 'TFE' in scanID:
        scan = 'T1'
    elif 'T2' in scanID or 'TSE' in scanID:
        scan = 'T2'
    elif 'DwiSE' in scanID:
        scan = 'dwi'
    elif 'FEEPI' in scanID:
        scan = 'func'
    else:
        scan = 'unknownScan'

    return (scan)


def getScanTime(parFile):
    '''
    Gets Water Fat Shift from Philips' PAR/XML Header.
    This uses the RegEx 'Scan Duration [sec]' string
    and searches for the corresponding integer for this value.
    Returns integer.
    '''
    scanTime = 'unknown'
    regexp = re.compile(
        r'.    Scan Duration \[sec\]                :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(parFile) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scanTime = match.group(1)
                scanTime = float(scanTime)
    return (scanTime)


def getEcho(jsonFile):
    '''
    Gets the echo time (TE) from a 
    JSON sidecar file for an acquisition.
    '''
    with open(jsonFile, "r") as read_file:
        data = json.load(read_file)

    echo = data.get("EchoTime")

    return (echo)


def convert_par_file(parFile, out_dir, basename):
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
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{parFile}"])

    # Get filenames
    dirPath = os.path.join(out_dir, basename)
    niiFile = glob.glob(dirPath + '*.nii*')
    jsonFile = glob.glob(dirPath + '*.json')

    # Convert lists to strings
    niiFile = ''.join(niiFile)
    jsonFile = ''.join(jsonFile)

    return (niiFile, jsonFile)


def convert_par_dwi(parFile, out_dir, basename):
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
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{parFile}"])

    # Get filenames
    dirPath = os.path.join(out_dir, basename)
    niiFile = glob.glob(dirPath + '*.nii*')
    jsonFile = glob.glob(dirPath + '*.json')
    bval = glob.glob(dirPath + '*.bval')
    bvec = glob.glob(dirPath + '*.bvec')

    # Convert lists to strings
    niiFile = ''.join(niiFile)
    jsonFile = ''.join(jsonFile)
    bval = ''.join(bval)
    bvec = ''.join(bvec)

    return (niiFile, jsonFile, bval, bvec)


def convert_par_fmap(parFile, out_dir, basename):
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
        ["dcm2niix", "-f", f"{basename}", "-b", "y", "-ba", "y", "-o", f"{out_dir}", "-z", "y", f"{parFile}"])

    # Get filenames
    dirPath = os.path.join(out_dir, basename)
    niiReal = glob.glob(dirPath + '*real*.nii*')
    jsonReal = glob.glob(dirPath + '*real*.json')
    niiMag = glob.glob(dirPath + '.nii*')
    jsonMag = glob.glob(dirPath + '.json')

    # Convert lists to strings
    niiReal = ''.join(niiReal)
    jsonReal = ''.join(jsonReal)
    niiMag = ''.join(niiMag)
    jsonMag = ''.join(jsonMag)

    return (niiReal, jsonReal, niiMag, jsonMag)


def data2BIDS_anat(out_dir, parFile, sub, scan, ses=1, scanType='anat'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scanType}")

    # Make output directory
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [niiFile, jsonFile] = convert_par_file(parFile, tmp_out_dir, tmp_basename)

    niiFile = os.path.abspath(niiFile)
    jsonFile = os.path.abspath(jsonFile)

    # Append w to T1/T2 if not already done
    if scan in 'T1' or scan in 'T2':
        scan = scan + 'w'
    else:
        scan = scan

    # Get Run number
    run = getNumRuns(outDir, scan=scan)
    run = '{:02}'.format(run)

    # Additional sequence/modality parameters
    epiFactor = getEPIfactor(parFile)
    wfs = getWFS(parFile)
    bval = getBval(parFile)
    acc = getAcc(parFile)
    mb = getMB(parFile)
    sct = getScanTime(parFile)

    # update JSON file with additional parameters
    jsonFile = updateJSON(jsonFile, bval, wfs, epiFactor, acc, mb, sct)

    # Create output filenames
    outName = f"sub-{sub}_ses-{ses}_run-{run}_{scan}"
    outNii = os.path.join(outDir, outName + '.nii.gz')
    outJson = os.path.join(outDir, outName + '.json')

    os.rename(niiFile, outNii)
    os.rename(jsonFile, outJson)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data2BIDS_func(out_dir, parFile, sub, ses=1, scanType='func', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scanType}")

    # Make output directory
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [niiFile, jsonFile] = convert_par_file(parFile, tmp_out_dir, tmp_basename)

    niiFile = os.path.abspath(niiFile)
    jsonFile = os.path.abspath(jsonFile)

    # Decide if file is 4D timeseries or single-band reference
    numFrames = getNumFrames(niiFile)
    if numFrames == 1:
        acq = 'AP'
        run = getNumRuns(outDir, scan='sbref', acq=acq, task=task)
        run = '{:02}'.format(run)
        outName = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_sbref"
    else:
        run = getNumRuns(outDir, scan='bold', acq=acq, task=task)
        run = '{:02}'.format(run)
        outName = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_bold"

    # Additional sequence/modality parameters
    epiFactor = getEPIfactor(parFile)
    wfs = getWFS(parFile)
    bval = getBval(parFile)
    acc = getAcc(parFile)
    mb = getMB(parFile)
    sct = getScanTime(parFile)

    # update JSON file with additional parameters
    jsonFile = updateJSON(jsonFile, bval, wfs, epiFactor, acc, mb, sct)

    # Create output filenames
    outNii = os.path.join(outDir, outName + '.nii.gz')
    outJson = os.path.join(outDir, outName + '.json')

    os.rename(niiFile, outNii)
    os.rename(jsonFile, outJson)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data2BIDS_fmap(out_dir, parFile, sub, ses=1, scanType='fmap', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scanType}")

    # Make output directory
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Convert PAR file
    [niiReal, jsonReal, niiMag, jsonMag] = convert_par_fmap(parFile, tmp_out_dir, tmp_basename)

    niiReal = os.path.abspath(niiReal)
    jsonReal = os.path.abspath(jsonReal)
    niiMag = os.path.abspath(niiMag)
    jsonMag = os.path.abspath(jsonMag)

    # Additional sequence/modality parameters
    epiFactor = getEPIfactor(parFile)
    wfs = getWFS(parFile)
    bval = getBval(parFile)
    acc = getAcc(parFile)
    mb = getMB(parFile)
    sct = getScanTime(parFile)

    # update JSON file with additional parameters
    jsonReal = updateJSON(jsonReal, bval, wfs, epiFactor, acc, mb, sct)
    jsonMag = updateJSON(jsonMag, bval, wfs, epiFactor, acc, mb, sct)

    # Get run number
    run = getNumRuns(outDir, scan='magnitude', acq=acq, task=task)
    run = '{:02}'.format(run)

    # Create output names
    outReal = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_fieldmap"
    outMag = f"sub-{sub}_ses-{ses}_task-{task}_dir-{acq}_run-{run}_magnitude"

    outRealNii = os.path.join(outDir, outReal + '.nii.gz')
    outMagNii = os.path.join(outDir, outMag + '.nii.gz')

    outRealJson = os.path.join(outDir, outReal + '.json')
    outMagJson = os.path.join(outDir, outMag + '.json')

    os.rename(niiReal, outRealNii)
    os.rename(niiMag, outMagNii)

    os.rename(jsonReal, outRealJson)
    os.rename(jsonMag, outMagJson)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data2BIDS_dwi(out_dir, parFile, sub, ses=1, scanType='dwi', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Create Output Directory Variables
    ses = '{:03}'.format(ses)
    out_dir = os.path.abspath(out_dir)
    outDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", f"{scanType}")

    # Make output directory
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Create temporary output names/directories
    tmp_out_dir = os.path.join(out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
    tmp_basename = 'tmp_basename' + str(random.randint(0, n))

    # Additional sequence/modality parameters
    epiFactor = getEPIfactor(parFile)
    wfs = getWFS(parFile)
    bval = getBval(parFile)
    acc = getAcc(parFile)
    mb = getMB(parFile)
    sct = getScanTime(parFile)

    # IF statement to handle either a B0 or b > 0 acquisition.
    if bval == 0:
        # Convert PAR file
        [niiFile, jsonFile] = convert_par_file(parFile, tmp_out_dir, tmp_basename)

        niiFile = os.path.abspath(niiFile)
        jsonFile = os.path.abspath(jsonFile)

        # Hard-coded to differentiate between the 
        # different echo B0s of the b800 or b2000
        # acquisitions.
        echo = getEcho(jsonFile)
        if echo < 0.093:
            dirs = 6
        else:
            dirs = 7
        dirs = '{:03}'.format(dirs)

        # update JSON file with additional parameters
        jsonFile = updateJSON(jsonFile, bval, wfs, epiFactor, acc, mb, sct)

        # Get Run Number
        acq = 'AP'
        run = getNumRuns(outDir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
        run = '{:02}'.format(run)
        outName = f"sub-{sub}_ses-{ses}_dir-{acq}_acq-{dirs}dirs_bval-b{bval}_run-{run}_dwi"

        # Create output filenames
        outNii = os.path.join(outDir, outName + '.nii.gz')
        outJson = os.path.join(outDir, outName + '.json')

        os.rename(niiFile, outNii)
        os.rename(jsonFile, outJson)
    else:
        # Convert PAR file
        [niiFile, jsonFile, bvals, bvecs] = convert_par_dwi(parFile, tmp_out_dir, tmp_basename)

        niiFile = os.path.abspath(niiFile)
        jsonFile = os.path.abspath(jsonFile)
        bvals = os.path.abspath(bvals)
        bvecs = os.path.abspath(bvecs)

        # Number of directions for CCHMC diffusion protocol correspond
        # to the number of frames in the 4D nifti file.
        # This information can also be obtained from the PAR/XML REC Header
        dirs = getNumFrames(niiFile)
        dirs = '{:03}'.format(dirs)

        # update JSON file with additional parameters
        jsonFile = updateJSON(jsonFile, bval, wfs, epiFactor, acc, mb, sct)

        # Get Run Number
        run = getNumRuns(outDir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
        run = '{:02}'.format(run)
        outName = f"sub-{sub}_ses-{ses}_dir-{acq}_acq-{dirs}dirs_bval-b{bval}_run-{run}_dwi"

        # Create output filenames
        outNii = os.path.join(outDir, outName + '.nii.gz')
        outJson = os.path.join(outDir, outName + '.json')
        outBvals = os.path.join(outDir, outName + '.bval')
        outBvecs = os.path.join(outDir, outName + '.bvec')

        os.rename(niiFile, outNii)
        os.rename(jsonFile, outJson)
        os.rename(bvals, outBvals)
        os.rename(bvecs, outBvecs)

    # remove temporary directory and leftover files
    shutil.rmtree(tmp_out_dir)


def data2BIDS_unknown(out_dir, parFile, sub, ses=1):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Get Acquisition Technique from PAR/REC
    # Header.
    scan = scanTech(parFile)

    # Convert PAR file
    if 'T1' in scan:
        try:
            data2BIDS_anat(out_dir, parFile, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'T2' in scan:
        try:
            data2BIDS_anat(out_dir, parFile, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'func' in scan:
        try:
            data2BIDS_func(out_dir, parFile, sub, ses=ses)
        except UnboundLocalError:
            pass
    elif 'dwi' in scan:
        try:
            data2BIDS_dwi(out_dir, parFile, sub, ses=ses)
        except UnboundLocalError:
            pass
    else:
        try:
            data2BIDS_anat(out_dir, parFile, sub, scan='unknownScan', scanType='unknown', ses=ses)
        except UnboundLocalError:
            pass
