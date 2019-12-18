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

# Random integer max range value
n = 10000


def getBval(dcmDir):
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
    ds = pydicom.dcmread(dcmDir)

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


def getAcc(dcmDir):
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
    ds = pydicom.dcmread(dcmDir)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'SENSE .*?([0-9.-]+)', line, re.M | re.I)
    if match:
        acc = match.group(1)
        acc = float(acc)

    return (acc)


def getMB(dcmDir):
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
    ds = pydicom.dcmread(dcmDir)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'MB.*?([0-9.-]+)', line, re.M | re.I)
    if match:
        mb = match.group(1)
        mb = int(mb)

    return (mb)


def getScanTime(dcmdir):
    '''
    Gets the scan time (s) from
    dicom data.
    '''

    # Load data
    ds = pydicom.dcmread(dcmdir)

    # Gets scan time
    try:
        scanTime = ds.AcquisitionDuration
    except AttributeError:
        pass
        scanTime = 'unknown'

    return (scanTime)


def updateJSON(jsonFile, bvalue='unknown', acc=1, mb=1, scanTime='unknown'):
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

    data = {"AccelerationFactor": acc, "MultiBandFactor": mb,
            "bvalue": bvalue, "ScanTime": scanTime,
            "SourceDataFormat": "DICOM"}

    with open(jsonFile, "r") as read_file:
        data2 = json.load(read_file)

    data2.update(data)

    with open(jsonFile, 'w+') as out_file:
        json.dump(data2, out_file, indent=4)

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


def getNumFrames(niiFile):
    '''Gets the number of frames for a DW or fMR image series.'''

    numFrames = subprocess.check_output(["fslval", niiFile, "dim4"])
    numFrames = str(numFrames)
    numFrames = int(re.sub('[^0-9]', '', numFrames))  # Strip non-numeric information
    return (numFrames)


def getScanName(dcmDir):
    '''
    Extracts scan name/type 
    from file description in the DICOM 
    header for philips MR scanners.
    Input is either dicom file or 
    dicom directory.
    '''

    # Load dicom data
    ds = pydicom.dcmread(dcmDir)

    # Get image descriptor
    scanID = ds.SeriesDescription
    # match = re.search(r'SENSE .*?([0-9.-]+)', line, re.M|re.I)
    if 'T1' in scanID or 'TFE' in scanID:
        scan = 'T1'
    elif 'T2' in scanID or 'TSE' in scanID:
        scan = 'T2'
    elif 'DwiSE' in scanID or 'DTI' in scanID or 'dti' in scanID or 'DWI' in scanID:
        scan = 'dwi'
    elif 'FEEPI' in scanID or 'fMR' in scanID:
        scan = 'func'
    else:
        scan = 'unknownScan'

    return (scan)


def getEcho(jsonFile):
    '''
    Gets the echo time (TE) from a 
    JSON sidecar file for an acquisition.
    '''
    with open(jsonFile, "r") as read_file:
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
    dirPath = os.path.join(out_dir, basename)
    adcNii = glob.glob(dirPath + '*ADC*.nii*')
    adcNii = ''.join(adcNii)
    if os.path.isfile(adcNii):
        os.remove(adcNii)

    # Get filenames
    dirPath = os.path.join(out_dir, basename)
    niiFile = glob.glob(dirPath + '*.nii*')
    jsonFile = glob.glob(dirPath + '*.json')

    # Convert lists to strings
    niiFile = ''.join(niiFile)
    jsonFile = ''.join(jsonFile)

    return (niiFile, jsonFile)


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
    dirPath = os.path.join(out_dir, basename)
    adcNii = glob.glob(dirPath + '*ADC*.nii*')
    adcNii = ''.join(adcNii)
    if os.path.isfile(adcNii):
        os.remove(adcNii)

    # Get filenames
    niiFile = glob.glob(dirPath + '.nii*')
    jsonFile = glob.glob(dirPath + '.json')
    bval = glob.glob(dirPath + '*.bval')
    bvec = glob.glob(dirPath + '*.bvec')

    # Convert lists to strings
    niiFile = ''.join(niiFile)
    jsonFile = ''.join(jsonFile)
    bval = ''.join(bval)
    bvec = ''.join(bvec)

    return (niiFile, jsonFile, bval, bvec)


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
    dirPath = os.path.join(out_dir, basename)
    niiReal = glob.glob(dirPath + '*e1.nii*')
    jsonReal = glob.glob(dirPath + '*e1.json')
    niiMag = glob.glob(dirPath + '*e1a.nii*')
    jsonMag = glob.glob(dirPath + '*e1a.json')

    # Convert lists to strings
    niiReal = ''.join(niiReal)
    jsonReal = ''.join(jsonReal)
    niiMag = ''.join(niiMag)
    jsonMag = ''.join(jsonMag)

    return (niiReal, jsonReal, niiMag, jsonMag)


def data2BIDS_anat(out_dir, dcm, sub, scan, ses=1, scanType='anat'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    try:
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

        # Convert DCM file
        [niiFile, jsonFile] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

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
        bval = getBval(dcm)
        acc = getAcc(dcm)
        mb = getMB(dcm)
        sct = getScanTime(dcm)

        # update JSON file with additional parameters
        jsonFile = updateJSON(jsonFile, bval, acc, mb, sct)

        # Create output filenames
        outName = f"sub-{sub}_ses-{ses}_run-{run}_{scan}"
        outNii = os.path.join(outDir, outName + '.nii.gz')
        outJson = os.path.join(outDir, outName + '.json')

        os.rename(niiFile, outNii)
        os.rename(jsonFile, outJson)

        # remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)
    except:
        pass


def data2BIDS_func(out_dir, dcm, sub, ses=1, scanType='func', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    try:
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

        # Convert DCM file
        [niiFile, jsonFile] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

        niiFile = os.path.abspath(niiFile)
        jsonFile = os.path.abspath(jsonFile)

        # Decide if file is 4D timeseries or single-band reference
        numFrames = getNumFrames(niiFile)
        if numFrames == 1:
            acq = 'AP'
            run = getNumRuns(outDir, scan='sbref', acq=acq, task=task)
            run = '{:02}'.format(run)
            outName = f"sub-{sub}_ses-{ses}_task-{task}_acq-{acq}_run-{run}_sbref"
        else:
            run = getNumRuns(outDir, scan='bold', acq=acq, task=task)
            run = '{:02}'.format(run)
            outName = f"sub-{sub}_ses-{ses}_task-{task}_acq-{acq}_run-{run}_bold"

        # Additional sequence/modality parameters
        bval = getBval(dcm)
        acc = getAcc(dcm)
        mb = getMB(dcm)
        sct = getScanTime(dcm)

        # update JSON file with additional parameters
        jsonFile = updateJSON(jsonFile, bval, acc, mb, sct)

        # Create output filenames
        outNii = os.path.join(outDir, outName + '.nii.gz')
        outJson = os.path.join(outDir, outName + '.json')

        os.rename(niiFile, outNii)
        os.rename(jsonFile, outJson)

        # remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)
    except:
        pass


def data2BIDS_fmap(out_dir, dcm, sub, ses=1, scanType='fmap', task='rest', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    try:
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

        # Convert DCM file
        [niiReal, jsonReal, niiMag, jsonMag] = convert_dcm_fmap(dcm, tmp_out_dir, tmp_basename)

        niiReal = os.path.abspath(niiReal)
        jsonReal = os.path.abspath(jsonReal)
        niiMag = os.path.abspath(niiMag)
        jsonMag = os.path.abspath(jsonMag)

        # Additional sequence/modality parameters
        bval = getBval(dcm)
        acc = getAcc(dcm)
        mb = getMB(dcm)
        sct = getScanTime(dcm)

        # update JSON file with additional parameters
        jsonReal = updateJSON(jsonReal, bval, acc, mb, sct)
        jsonMag = updateJSON(jsonMag, bval, acc, mb, sct)

        # Get run number
        run = getNumRuns(outDir, scan='magnitude', acq=acq, task=task)
        run = '{:02}'.format(run)

        # Create output names
        outReal = f"sub-{sub}_ses-{ses}_task-{task}_acq-{acq}_run-{run}_fieldmap"
        outMag = f"sub-{sub}_ses-{ses}_task-{task}_acq-{acq}_run-{run}_magnitude"

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
    except:
        pass


def data2BIDS_dwi(out_dir, dcm, sub, ses=1, scanType='dwi', acq='PA'):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    try:
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
        bval = getBval(dcm)
        acc = getAcc(dcm)
        mb = getMB(dcm)
        sct = getScanTime(dcm)

        # IF statement to handle either a B0 or b > 0 acquisition.
        if bval == 0:
            # Convert dcm file
            [niiFile, jsonFile] = convert_dcm(dcm, tmp_out_dir, tmp_basename)

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
            jsonFile = updateJSON(jsonFile, bval, acc, mb, sct)

            # Get Run Number
            acq = 'AP'
            run = getNumRuns(outDir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
            run = '{:02}'.format(run)
            outName = f"sub-{sub}_ses-{ses}_acq-{acq}_dirs-{dirs}_bval-b{bval}_run-{run}_dwi"

            # Create output filenames
            outNii = os.path.join(outDir, outName + '.nii.gz')
            outJson = os.path.join(outDir, outName + '.json')

            os.rename(niiFile, outNii)
            os.rename(jsonFile, outJson)
        else:
            # Convert dcm file
            [niiFile, jsonFile, bvals, bvecs] = convert_dcm_dwi(dcm, tmp_out_dir, tmp_basename)

            niiFile = os.path.abspath(niiFile)
            jsonFile = os.path.abspath(jsonFile)
            bvals = os.path.abspath(bvals)
            bvecs = os.path.abspath(bvecs)

            # Number of directions for CCHMC diffusion protocol correspond
            # to the number of frames in the 4D nifti file.
            dirs = getNumFrames(niiFile)
            dirs = '{:03}'.format(dirs)

            # update JSON file with additional parameters
            jsonFile = updateJSON(jsonFile, bval, acc, mb, sct)

            # Get Run Number
            run = getNumRuns(outDir, scan='dwi', acq=acq, dirs=dirs, bval=bval)
            run = '{:02}'.format(run)
            outName = f"sub-{sub}_ses-{ses}_acq-{acq}_dirs-{dirs}_bval-b{bval}_run-{run}_dwi"

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
    except:
        pass


def data2BIDS_unknown(out_dir, dcm, sub, ses=1):
    '''
    Renames converted nifti files to conform with BIDS format
    (in the case of anatomical files).
    NB: out_dir refers to the parent or RawData directory.
    '''

    # Get Acquisition Technique from dicom
    # Header.
    scan = getScanName(dcm)

    # Convert DCM file
    if 'T1' in scan:
        try:
            data2BIDS_anat(out_dir, dcm, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'T2' in scan:
        try:
            data2BIDS_anat(out_dir, dcm, sub, scan=scan, ses=ses)
        except UnboundLocalError:
            pass
    elif 'func' in scan:
        try:
            data2BIDS_func(out_dir, dcm, sub, ses=ses)
        except UnboundLocalError:
            pass
    elif 'dwi' in scan:
        try:
            data2BIDS_dwi(out_dir, dcm, sub, ses=ses)
        except UnboundLocalError:
            pass
    else:
        try:
            data2BIDS_anat(out_dir, dcm, sub, scan='unknownScan', scanType='unknown', ses=ses)
        except UnboundLocalError:
            pass
