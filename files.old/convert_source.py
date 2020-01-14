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


def convert_par(out_dir, par_file, sub, ses=1):
    '''convert PAR file to BIDS nifti based on filename.'''
    if 'T1' in par_file:
        try:
            csp.data_to_bids_anat(out_dir, par_file, sub, scan='T1', ses=ses)
        except ValueError:
            pass
    elif 'T2' in par_file:
        try:
            csp.data_to_bids_anat(out_dir, par_file, sub, scan='T2', ses=ses)
        except ValueError:
            pass
    elif 'SWI' in par_file:
        try:
            csp.data_to_bids_anat(out_dir, par_file, sub, scan='SWI', scanType='fmap', ses=ses)
        except ValueError:
            pass
    elif 'vis' in par_file or 'Vis' in par_file or 'VIS' in par_file:
        try:
            csp.data_to_bids_func(out_dir, par_file, sub, ses, task='visualstrobe')
        except ValueError:
            pass
    elif 'rsfMR' in par_file or 'rsf' in par_file:
        try:
            csp.data_to_bids_func(out_dir, par_file, sub, ses, task='rest')
        except ValueError:
            pass
    elif 'map' in par_file or 'Map' in par_file or 'MAP' in par_file:
        try:
            csp.data_to_bids_fmap(out_dir, par_file, sub, ses)
        except ValueError:
            pass
    elif 'dti' in par_file or 'DTI' in par_file or 'dwi' in par_file or 'DWI' in par_file:
        try:
            csp.data_to_bids_dwi(out_dir, par_file, sub, ses)
        except ValueError:
            pass
    else:
        try:
            csp.data_to_bids_unknown(out_dir, par_file, sub, ses)
        except ValueError:
            pass


def par_batch(par_files, out_dir, sub, ses=1, verbose=False):
    '''
    par_files is a list of par_files.
    This should not be run in parallel.
    '''
    for par_file in par_files:
        if verbose in [True]:
            print(par_file)
        convert_par(out_dir, par_file, sub, ses)

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
        unknown_dir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", "unknown", "*.nii*")
        num_files = glob.glob(unknown_dir)
        print("")
        print(f"Number of unknown modalities for sub-{sub}_ses-{ses}: {num_files}")
        print("")


def exclude_par(data_dir, config_exclude=''):
    '''
    Takes the PAR REC (parent directory), and creates
    a list of PAR header files for conversion.
    Certain files/modalities/sequences can be 
    excluded via the exclude.yml file
    '''

    # YML file format for exclusion:
    # exclude: SWI,SURVEY,Reg

    # data_dir = csp.renamePAR_REC_Dir(data_dir)

    # Create List of PAR Files
    par_file_headers = os.path.join(data_dir, "*.PAR")
    par_files = glob.glob(par_file_headers, recursive=True)

    if pathlib.Path(config_exclude).exists():
        # Load in exclusion config file
        with open(config_exclude) as f:
            data_map = yaml.safe_load(f)

        # Create seculded exclusion dictionary
        exclude_ = [[k, v] for k, v in data_map.items()]

        # Create Set of PAR files
        par_set = set(par_files)

        # Find difference in sets (e.g. PAR_s \ exclude_s)
        for ex in exclude_:
            ex = (exclude_[0])
            ex_tmp = ex[1:2]
            exs = ex_tmp[0].split(",")

            for x in exs:
                dir_ = os.path.join(data_dir, f"*{x}*.PAR")
                ex_set = set(glob.glob(dir_, recursive=True))
                par_set = par_set.difference(ex_set)

        par_files_included = list(par_set)
    else:
        par_files_included = par_files

    return (par_files_included)


def sub_par(sub, par_dir, out_put_bids, ses=1, config='', verbose=False):
    '''
    SUBject PAR conversion function.
    par_dir is PAR REC directory.
    The PAR REC files are batch-
    converted to nifti BIDS format.
    '''

    par_files = exclude_par(par_dir, config)

    par_batch(par_files, out_put_bids, sub, ses, verbose)


def convert_dcm(out_dir, dcm, sub, ses=1):
    '''convert dicom file to BIDS nifti based on filename.'''
    if 'T1' in dcm:
        try:
            cdm.data_to_bids_anat(out_dir, dcm, sub, scan='T1', ses=ses)
        except ValueError:
            pass
    elif 'T2' in dcm:
        try:
            cdm.data_to_bids_anat(out_dir, dcm, sub, scan='T2', ses=ses)
        except ValueError:
            pass
    elif 'SWI' in dcm:
        try:
            cdm.data_to_bids_anat(out_dir, dcm, sub, scan='SWI', scanType='fmap', ses=ses)
        except ValueError:
            pass
    elif 'vis' in dcm or 'Vis' in dcm or 'VIS' in dcm:
        try:
            cdm.data_to_bids_func(out_dir, dcm, sub, ses, task='visualstrobe')
        except ValueError:
            pass
    elif 'rsfMR' in dcm or 'rsf' in dcm:
        try:
            cdm.data_to_bids_func(out_dir, dcm, sub, ses, task='rest')
        except ValueError:
            pass
    elif 'map' in dcm or 'Map' in dcm or 'MAP' in dcm:
        try:
            cdm.data_to_bids_fmap(out_dir, dcm, sub, ses)
        except ValueError:
            pass
    elif 'dti' in dcm or 'DTI' in dcm or 'dwi' in dcm or 'DWI' in dcm or 'B0' in dcm or 'b0' in dcm:
        try:
            cdm.data_to_bids_dwi(out_dir, dcm, sub, ses)
        except ValueError:
            pass
    else:
        try:
            cdm.data_to_bids_unknown(out_dir, dcm, sub, ses)
        except ValueError:
            pass


def get_dcm_file(dcm_dir):
    '''
    Goes to the specified dicom
    directory and returns the 
    first dicom file.
    '''

    dcm_dir = os.path.abspath(dcm_dir)
    # os.chdir(dcm_dir)
    dcm_dir_list = glob.glob(dcm_dir + '*/*', recursive=True)

    # Initilized dcm_file
    dcm_file = ""

    for file in dcm_dir_list:
        dcm_file = os.path.abspath(file)
        # print(dcm_file)
        break

    return (dcm_file)


def dcm_batch(dcms, out_dir, sub, ses=1, verbose=False):
    '''
    dcms is a list of dcm directories.
    This should not be run in parallel.
    '''
    for dcm in dcms:
        if verbose in [True]:
            print(dcm)
        dcm_file = get_dcm_file(dcm)
        is_valid = is_valid_mr(dcm_file)
        if is_valid in [True]:
            convert_dcm(out_dir, dcm_file, sub, ses)

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
        unknown_dir = os.path.join(out_dir, f"sub-{sub}", f"ses-{ses}", 'unknown', "*.nii*")
        num_files = len(glob.glob(unknown_dir))
        print("")
        print(f"Number of unknown modalities for sub-{sub}_ses-{ses}: {num_files}")
        print("")


def exclude_dcm(data_dir, config_exclude=''):
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
    dcm_dirs = glob.glob(data_dir + '*/*', recursive=True)

    if pathlib.Path(config_exclude).exists():
        # Load in exclusion config file
        with open(config_exclude) as f:
            data_map = yaml.safe_load(f)

        # Create seculded exclusion dictionary
        exclude_ = [[k, v] for k, v in data_map.items()]

        # Create Set of DICOM directories
        dcm_set = set(dcm_dirs)

        # Find difference in sets (e.g. DCM_s \ exclude_s)
        for ex in exclude_:
            ex = (exclude_[0])
            ex_tmp = ex[1:2]
            exs = ex_tmp[0].split(",")

            for x in exs:
                dir_ = os.path.join(data_dir, f"*{x}*")
                ex_set = set(glob.glob(dir_, recursive=True))
                dcm_set = dcm_set.difference(ex_set)

        dcm_dirs_included = list(dcm_set)
    else:
        dcm_dirs_included = dcm_dirs

    return (dcm_dirs_included)


def is_valid_mr(dcm):
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
    is_valid = ds.ConversionType

    if is_valid in '':
        is_valid = True
    else:
        is_valid = False
        print(
            f"Please check Conversion Type (0008, 0064) in dicom header. The presented DICOM file is not a valid file: {dcm}.")

    return (is_valid)


def sub_dcm(sub, par_dir, out_put_bids, ses=1, config='', verbose=False):
    '''
    SUBject DiCoM conversion function.
    par_dir is parent DICOM directory.
    The DICOM files are batch-
    converted to nifti BIDS format.
    '''

    dcm_files = exclude_dcm(par_dir, config)

    dcm_batch(dcm_files, out_put_bids, sub, ses, verbose)


if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(
        description='Script to perform source data conversion from either PAR REC or DICOM to BIDS NifTi.')

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
                            dest="data_dir",
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
        sub_par(sub=args.sub, par_dir=args.data_dir, out_put_bids=args.out_bids, ses=args.ses, config=args.exCfg,
               verbose=args.verbose)
    elif args.conv == 'DCM':
        sub_dcm(sub=args.sub, par_dir=args.data_dir, out_put_bids=args.out_bids, ses=args.ses, config=args.exCfg,
               verbose=args.verbose)
    else:
        print(
            "Option not recognized. Please use the \'--fileType\' option with either \'PAR\' or \'DCM\' as specified.")
