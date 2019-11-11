#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-
# title           : convertSource.py
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2019 08 16 13:37:19
# version         : 0.0.x
# usage           : convertSource.py [-h,--help]
# notes           : [notes]
# python_version  : 3.7.3
# ==============================================================================

# Import Packages & Modules

import os
import shutil
import glob
import pathlib
import yaml
import pydicom
import argparse

# Import custom conversion modules
import convertSourcePAR as csp  # PAR REC file conversion
import convertSourceDCM as cdm  # Phlips DICOM file conversion


def convertPAR(out_dir, parFile, sub, ses=1):
    '''convert PAR file to BIDS nifti based on filename.'''
    if 'T1' in parFile:
        try:
            csp.data2BIDS_anat(out_dir, parFile, sub, scan='T1', ses=ses)
        except:
            pass
    elif 'T2' in parFile:
        try:
            csp.data2BIDS_anat(out_dir, parFile, sub, scan='T2', ses=ses)
        except:
            pass
    elif 'SWI' in parFile:
        try:
            csp.data2BIDS_anat(out_dir, parFile, sub, scan='SWI', scanType='fmap', ses=ses)
        except:
            pass
    elif 'vis' in parFile or 'Vis' in parFile or 'VIS' in parFile:
        try:
            csp.data2BIDS_func(out_dir, parFile, sub, ses, task='visualstrobe')
        except:
            pass
    elif 'rsfMR' in parFile or 'rsf' in parFile:
        try:
            csp.data2BIDS_func(out_dir, parFile, sub, ses, task='rest')
        except:
            pass
    elif 'map' in parFile or 'Map' in parFile or 'MAP' in parFile:
        try:
            csp.data2BIDS_fmap(out_dir, parFile, sub, ses)
        except:
            pass
    elif 'dti' in parFile or 'DTI' in parFile or 'dwi' in parFile or 'DWI' in parFile:
        try:
            csp.data2BIDS_dwi(out_dir, parFile, sub, ses)
        except:
            pass
    else:
        try:
            csp.data2BIDS_unknown(out_dir, parFile, sub, ses)
        except:
            pass


def parBatch(parFiles, out_dir, sub, ses=1, verbose=False):
    '''
    parFiles is a list of parFiles.
    This should not be run in parallel.
    '''
    for parFile in parFiles:
        if verbose in [True]:
            print(parFile)
        convertPAR(out_dir, parFile, sub, ses)

    # Check for leftover temporary directories
    dirs_ = os.path.join(out_dir, f"sub-{sub}",'*tmp*')
    sub_dirs_ = glob.glob(dirs_)

    # Temporary directory clean-up
    if len(sub_dirs_) >= 1:
        for sub_dir_ in sub_dirs_:
            shutil.rmtree(sub_dir_)

    # Check for number of files in unknown
    if verbose in [True]:
        ses = '{:03}'.format(ses)
        unknwnDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", "unknown", "*.nii*")
        numFiles = glob.glob(unknwnDir)
        print("")
        print(f"Number of unknown modalities for sub-{sub}_ses-{ses}: {numFiles}")
        print("")


def excludePAR(dataDir, configExclude='exclude.yml'):
    '''
    Takes the PAR REC (parent directory), and creates
    a list of PAR header files for conversion.
    Certain files/modalities/sequences can be 
    excluded via the exclude.yml file
    '''

    # YML file format for exclusion:
    # exclude: SWI,SURVEY,Reg

    dataDir = csp.renamePAR_REC_Dir(dataDir)

    # Create List of PAR Files
    parFileHeaders = os.path.join(dataDir, "*.PAR")
    parFiles = glob.glob(parFileHeaders, recursive=True)

    if pathlib.Path(configExclude).exists():
        # Load in exclusion config file
        with open(configExclude) as f:
            dataMap = yaml.safe_load(f)

        # Create seculded exclusion dictionary
        exL = [[k, v] for k, v in dataMap.items()]

        # Create Set of PAR files
        parSet = set(parFiles)

        # Find difference in sets (e.g. PAR_s \ exclude_s)
        for ex in exL:
            ex = (exL[0])
            ex_tmp = ex[1:2]
            exs = ex_tmp[0].split(",")

            for x in exs:
                dir_ = os.path.join(dataDir, f"*{x}*.PAR")
                exSet = set(glob.glob(dir_, recursive=True))
                parSet = parSet.difference(exSet)

        parFilesincluded = list(parSet)
    else:
        parFilesincluded = parFiles

    return (parFilesincluded)


def subPAR(sub, parDir, out_put_BIDS, ses=1, config='exclude.yml', verbose=False):
    '''
    SUBject PAR conversion function.
    parDir is PAR REC directory.
    The PAR REC files are batch-
    converted to nifti BIDS format.
    '''

    parFiles = excludePAR(parDir, config)

    parBatch(parFiles, out_put_BIDS, sub, ses, verbose)


def convertDCM(out_dir, dcm, sub, ses=1):
    '''convert dicom file to BIDS nifti based on filename.'''
    if 'T1' in dcm:
        try:
            cdm.data2BIDS_anat(out_dir, dcm, sub, scan='T1', ses=ses)
        except:
            pass
    elif 'T2' in dcm:
        try:
            cdm.data2BIDS_anat(out_dir, dcm, sub, scan='T2', ses=ses)
        except:
            pass
    elif 'SWI' in dcm:
        try:
            cdm.data2BIDS_anat(out_dir, dcm, sub, scan='SWI', scanType='fmap', ses=ses)
        except:
            pass
    elif 'vis' in dcm or 'Vis' in dcm or 'VIS' in dcm:
        try:
            cdm.data2BIDS_func(out_dir, dcm, sub, ses, task='visualstrobe')
        except:
            pass
    elif 'rsfMR' in dcm or 'rsf' in dcm:
        try:
            cdm.data2BIDS_func(out_dir, dcm, sub, ses, task='rest')
        except:
            pass
    elif 'map' in dcm or 'Map' in dcm or 'MAP' in dcm:
        try:
            cdm.data2BIDS_fmap(out_dir, dcm, sub, ses)
        except:
            pass
    elif 'dti' in dcm or 'DTI' in dcm or 'dwi' in dcm or 'DWI' in dcm or 'B0' in dcm or 'b0' in dcm:
        try:
            cdm.data2BIDS_dwi(out_dir, dcm, sub, ses)
        except:
            pass
    else:
        try:
            cdm.data2BIDS_unknown(out_dir, dcm, sub, ses)
        except:
            pass


def getDCMfile(dcmDir):
    '''
    Goes to the specified dicom
    directory and returns the 
    first dicom file.
    '''

    dcmDir = os.path.abspath(dcmDir)
    # os.chdir(dcmDir)
    dcmDIRList = glob.glob(dcmDir + '*/*', recursive=True)

    # Initilized dcmFile
    dcmFile = ""

    for file in dcmDIRList:
        dcmFile = os.path.abspath(file)
        # print(dcmFile)
        break

    return (dcmFile)


def dcmBatch(dcms, out_dir, sub, ses=1, verbose=False):
    '''
    dcms is a list of dcm directories.
    This should not be run in parallel.
    '''
    for dcm in dcms:
        if verbose in [True]:
            print(dcm)
        dcmFile = getDCMfile(dcm)
        isValid = isValidMR(dcmFile)
        if isValid in [True]:
            convertDCM(out_dir, dcmFile, sub, ses)

    # Check for leftover temporary directories
    dirs_ = os.path.join(out_dir, f"sub-{sub}",'*tmp*')
    sub_dirs_ = glob.glob(dirs_)

    # Temporary directory clean-up
    if len(sub_dirs_) >= 1:
        for sub_dir_ in sub_dirs_:
            shutil.rmtree(sub_dir_)

    # Check for number of files in unknown
    if verbose in [True]:
        ses = '{:03}'.format(ses)
        unknwnDir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", 'unknown', "*.nii*")
        numFiles = len(glob.glob(unknwnDir))
        print("")
        print(f"Number of unknown modalities for sub-{sub}_ses-{ses}: {numFiles}")
        print("")


def excludeDCM(dataDir, configExclude='exclude.yml'):
    '''
    Takes the DICOM (parent directory), and creates
    a list of the first DICOM files from the parent 
    directory for conversion. Certain 
    files/modalities/sequences can be 
    excluded via the exclude.yml file
    '''

    # YML file format for exclusion:
    # exclude: SWI,SURVEY,Reg etc.

    # Create List of DICOM Files
    dcmDIRS = glob.glob(dataDir + '*/*', recursive=True)

    if pathlib.Path(configExclude).exists():
        # Load in exclusion config file
        with open(configExclude) as f:
            dataMap = yaml.safe_load(f)

        # Create seculded exclusion dictionary
        exL = [[k, v] for k, v in dataMap.items()]

        # Create Set of DICOM directories
        dcmSet = set(dcmDIRS)

        # Find difference in sets (e.g. DCM_s \ exclude_s)
        for ex in exL:
            ex = (exL[0])
            ex_tmp = ex[1:2]
            exs = ex_tmp[0].split(",")

            for x in exs:
                dir_ = os.path.join(dataDir, f"*{x}*")
                exSet = set(glob.glob(dir_, recursive=True))
                dcmSet = dcmSet.difference(exSet)

        dcmDIRSincluded = list(dcmSet)
    else:
        dcmDIRSincluded = dcmDIRS

    return (dcmDIRSincluded)


def isValidMR(dcm):
    '''
    Checks for valid DICOM file(s) by inspecting
    the ConversionType label in the dicom header.
    If this label is populated, then it is likely
    a secondary image capture, and is not likely
    an image that contains meaningful information.
    '''

    # Read dicom header
    ds = pydicom.dcmread(dcm)

    # Invalid files include secondary image captures, and are not suitable for 
    # nifti conversion.
    isValid = ds.ConversionType

    if isValid in '':
        isValid = True
    else:
        isValid = False
        print(
            f"Please check Conversion Type (0008, 0064) in dicom header. The presented DICOM file is not a valid file: {dcm}.")

    return (isValid)


def subDCM(sub, parDir, out_put_BIDS, ses=1, config='exclude.yml', verbose=False):
    '''
    SUBject DiCoM conversion function.
    parDir is parent DICOM directory.
    The DICOM files are batch-
    converted to nifti BIDS format.
    '''

    dcmFiles = excludeDCM(parDir, config)

    dcmBatch(dcmFiles, out_put_BIDS, sub, ses, verbose)


if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(
        description='Script to perform source data conversion from either PAR REC or DICOM to BIDS NifTi. This script is intended for the IRC 287 and 317 Neonatal studies and their corresponding imaging protocol(s).')

    # Parse Arguments
    # Required Arguments
    reqoptions = parser.add_argument_group('Required arguments')
    reqoptions.add_argument('-s', '-sub', '--sub',
                            type=str,
                            dest="sub",
                            metavar="subject_ID",
                            required=True,
                            help="Unique subject identifier given to each participant. This indentifier CAN contain letters and numbers. This identifier CANNOT contain: underscores, hyphens, colons, semi-colons, spaces, or any other special characters.")
    reqoptions.add_argument('-o', '-out', '--out',
                            type=str,
                            dest="out_bids",
                            metavar="Out_BIDS_Directory",
                            required=True,
                            help="BIDS output directory. This directory does not need to exist at runtime. The resulting directory will be populated with BIDS named and structured data.")

    reqoptions.add_argument('-d', '-data', '--data',
                            type=str,
                            dest="dataDir",
                            metavar="Data_Directory",
                            required=True,
                            help="Parent directory that contains that subuject's unconverted source data. This directory can contain either all the PAR REC files, or all the directories of the DICOM files. NOTE: filepaths with spaces either need to replaced with underscores or placed in quotes. NOTE: The PAR REC directory is rename PAR_REC automaticaly.")

    reqoptions.add_argument('-f', '-file', '--filetype',
                            type=str,
                            dest="conv",
                            metavar="FileType",
                            required=True,
                            help="File type that is to be used with the converter. Acceptable choices include either: PAR or DCM.")

    # Optional Arguments
    optoptions = parser.add_argument_group('Optional arguments')
    optoptions.add_argument('-ses', '--ses',
                            type=int,
                            dest="ses",
                            metavar="session",
                            required=False,
                            default=1,
                            help="Session label for the acquired source data. [default: 1]")
    optoptions.add_argument('-e', '-exclude', '--exclude',
                            type=str,
                            dest="exCfg",
                            metavar="Exclusion_Config.yml",
                            required=False,
                            default="",
                            help="YAML configuruation file that contains an exclusion list of specific modalities to avoid or not convert.")
    optoptions.add_argument('-v', '-verbose', '--verbose',
                            dest="verbose",
                            required=False,
                            action="store_true",
                            help="Prints additional information such as the current file being converted, the file(s) that were excluded as non-readable, and the number of files converted that had unknown modalities.")

    args = parser.parse_args()

    # Print help message in the case
    # of no arguments
    try:
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            parser.print_help()

    # Verbose flag
    if args.verbose:
        args.verbose = True

    # Convert Source Data Files
    if args.conv == 'PAR':
        subPAR(sub=args.sub, parDir=args.dataDir, out_put_BIDS=args.out_bids, ses=args.ses, config=args.exCfg,
               verbose=args.verbose)
    elif args.conv == 'DCM':
        subDCM(sub=args.sub, parDir=args.dataDir, out_put_BIDS=args.out_bids, ses=args.ses, config=args.exCfg,
               verbose=args.verbose)
    else:
        print(
            "Option not recognized. Please use the \'--fileType\' option with either \'PAR\' or \'DCM\' as specified.")
