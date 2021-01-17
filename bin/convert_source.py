#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-
# title           : convert_source.py
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2020 01 14 15:29:24
# version         : 0.0.3
# usage           : convert_source.py [-h,--help]
# notes           : [notes]
# python_version  : 3.7.4
#==============================================================================

# Import packages and modules
import os
import sys
import glob
import yaml
import argparse

from typing import List, Dict, Optional, Union, Tuple


# Import third party packages and modules
import convert_source_dcm as cdm
import convert_source_par as csp
import convert_source_nii as csn
import utils.file_utils

# Define functions
def read_config(config_file: str, 
                verbose: bool = False
                ) -> Tuple[Dict,List[str],Dict]:
    '''Reads configuration file and creates a dictionary of search terms for 
    certain modalities provided that BIDS modalities are used as keys. If
    exclusions are provided (via the key 'exclude') then an exclusion list is 
    created. Otherwise, 'exclusion_list' is returned as an empty list. If 
    additional settings are specified, they should be done so via the key
    'metadata' to enable writing of additional metadata. Otherwise, an 
    empty dictionary is returned.
    
    Arguments:
        config_file: file path to yaml configuration file.
        verbose: Prints additional information to screen.
    
    Returns: 
        search_dict: Nested dictionary of search terms for BIDS modalities
        exclusion_list: List of exclusion terms
        meta_dict: Nested dictionary of metadata terms to write to JSON file(s)
    '''
    
    with open(config_file) as file:
        data_map = yaml.safe_load(file)
        if verbose:
            print("Initialized parameters from configuration file")
    
    # Required search terms
    if any("search" in data_map for element in data_map):
        if verbose:
            print("Categorizing search terms")
        search_dict = data_map["search"]
        del data_map["search"]
    else:
        if verbose:
            print("Heuristic search terms required. Exiting...")
        sys.exit(1)
        
    if any("exclude" in data_map for element in data_map):
        if verbose:
            print("Exclusion option implemented")
        exclusion_list = data_map["exclude"]
        del data_map["exclude"]
    else:
        if verbose:
            print("Exclusion option not implemented")
        exclusion_list = list()
        
    if any("metadata" in data_map for element in data_map):
        if verbose:
            print("Including additional settings for metadata")
        meta_dict = data_map["metadata"]
        del data_map["metadata"]
    else:
        if verbose:
            print("No metadata settings")
        meta_dict = dict()
        
    return search_dict,exclusion_list,meta_dict

def create_file_list(data_dir, file_ext="", order="size"):
    '''
    Creates a file list by globbing a directory for a specific file
    extension and sorting by some determined order. A file list is 
    then returned
    
    Arguments:
        data_dir (string): Absolute path to data directory (must be a directory dump of image data)
        file_ext (string): File extension to glob. Built-in options include:
            - 'par' or 'PAR': Searches for PAR headers
            - 'dcm' or 'DICOM': Searches for DICOM directories, then searches for one file from each DICOM directory
            - 'nii', or 'Nifti': Searches for nifti files (including gzipped nifti files)
        order (string): Order to sort the list. Valid options are: 'size' and 'time':
            - 'size': sorts by file size in ascending order (default)
            - 'time': sorts by file modification time in ascending order
            - 'none': no sorting is applied and the list is generated as the system finds the files
    
    Returns: 
        file_list (list): List of filenames, complete with their absolute paths.
    '''
    
    # Check file extension
    if file_ext != "":
        if file_ext.upper() == "PAR" or file_ext.upper() == "REC":
            file_ext = "PAR"
            file_ext = f".{file_ext.upper()}"
        elif file_ext.lower() == "dcm" or file_ext.upper() == "DICOM":
            file_ext = "dcm"
            file_ext = f".{file_ext.lower()}"
        elif file_ext.lower() == "nii" or file_ext.lower() == "nifti":
            file_ext = "nii"
            file_ext = f".{file_ext.lower()}*" # Add wildcard for globbling gzipped files
        else:
            file_ext = f".{file_ext}"
    
    # Check sort order
    if order.lower() == "size":
        order_key = os.path.getsize
    elif order.lower() == "time":
        order_key = os.path.getmtime
    elif order.lower() == "none":
        order_key=None
    else:
        order_key = os.path.getsize
        print("Unrecognized keyword option. Using default.")
    
    # Create file list
    if file_ext == ".dcm":
        file_list = sorted(cdm.get_dcm_files(data_dir), key=order_key, reverse=False)
    elif file_ext != ".dcm":
        file_names = os.path.join(data_dir, f"*{file_ext}")
        file_list = sorted(glob.glob(file_names, recursive=True), key=order_key, reverse=False)
    
    return file_list

def file_exclude(file_list, data_dir, exclusion_list = [], verbose = False):
    '''
    Excludes files from the conversion process by removing filenames
    that contain words that match those found in the 'exclusion_list'
    from the 'read_config' function - should any files need/want to be 
    excluded.
    
    If 'exclusion_list' is empty, then the original 'file_list' is returned.
    
    Arguments:
        file_list (list): List of filenames
        data_dir (string): Absolute path to parent directory that contains the image data
        exclusion_list (list): List of words to be matched. Filenames that contain these words will be excluded.
        verbose (bool): Boolean - True or False.
    
    Returns: 
        currated_list (list): Currated list of filenames, with unwanted filenames removed.
    '''
            
    # Check file extension in file list
    if 'dcm' in file_list[0]:
        file_ext = "dcm"
        file_ext = f".{file_ext.lower()}"
    elif 'PAR' in file_list[0]:
        file_ext = "PAR"
        file_ext = f".{file_ext.upper()}"
    elif 'nii' in file_list[0]:
        file_ext = "nii"
        file_ext = f".{file_ext.lower()}*" # Add wildcard for globbling gzipped files
    else:
        file_ext = ""
        file_ext = f".{file_ext.lower()}"
    
    # create set of lists
    file_set = set(file_list)
    
    # create empty sets
    currated_set = set()
    exclusion_set = set()
    
    if len(exclusion_list) == 0:
        currated_set = file_set
    else:
        for file in exclusion_list:
            if file_ext == '.dcm':
                dir_ = os.path.join(data_dir, f"*{file}*",f"*{file_ext}")
            else:
                dir_ = os.path.join(data_dir, f"*{file}*{file_ext}")
            f_names = glob.glob(dir_, recursive=True)        
            f_names_set = set(f_names)
            if verbose:
                if len(f_names_set) != 0:
                    print(f"Excluded files: {f_names_set} \n")
            exclusion_set.update(f_names_set)
            
        currated_set = file_set.difference(exclusion_set)

    currated_list = list(currated_set)
    
    return currated_list

def get_scan_tech(bids_out_dir, sub, file, search_dict, meta_dict=dict(), ses=1, keep_unknown=True, verbose=False):
    '''
    Searches DICOM or PAR file header for scan technique/MR modality used in accordance with the search terms provided
    by the nested dictionary.
    
    Arguments:
        bids_out_dir (string): Output BIDS directory
        sub (int or string): Subject ID
        file (string): Source image filename with absolute filepath
        search_dict (dict): Nested dictionary from the 'read_config' function
        meta_dict (dict): Nested metadata dictionary
        ses (int or string): Session ID
        keep_unknown (bool): Convert modalities/scans which cannot be identified (default: True)
        verbose (bool): Prints the scan_type, modality, and search terms used (e.g. func - bold - rest - ['rest', 'FFE'])
    
    Returns: 
        None
    '''
    
    if not meta_dict:
        meta_dict = dict()

    converted_files = list()
    
    # Check file extension in file
    # Perform Scanning Techniqe Search
    if '.dcm' in file.lower():
        converted_files = cdm.get_dcm_scan_tech(bids_out_dir=bids_out_dir, sub=sub, dcm_file=file, search_dict=search_dict, meta_dict=meta_dict, ses=1, keep_unknown=keep_unknown, verbose=verbose)
    elif '.PAR' in file.upper():
        converted_files = csp.get_par_scan_tech(bids_out_dir=bids_out_dir, sub=sub, par_file=file, search_dict=search_dict, meta_dict=meta_dict, ses=1, keep_unknown=keep_unknown, verbose=verbose)
    else:
        if verbose:
            print("unknown modality")
        if keep_unknown:
            if verbose:
                print("converting unknown_modality")
            scan_type = 'unknown_modality'
            scan = 'unknown'
            [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type)
            converted_files = csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
        
    return converted_files

def convert_modality(bids_out_dir, sub, file, search_dict, meta_dict=dict(), ses=1, keep_unknown=True, verbose=False):
    '''
    Converts an image file and extracts information from the filename (such as the modality). 
    
    Note: This function is still undergoing active development.
    Note: Add support for extra dictionaries
    
    Arguments:
        bids_out_dir (string): Output BIDS directory
        sub (int or string): Subject ID
        file (string): Source image filename with absolute filepath
        search_dict (dict): Nested dictionary from the 'read_config' function
        meta_dict (dict): Nested metadata dictionary
        ses (int or string): Session ID
        keep_unknown (bool): Convert modalities/scans which cannot be identified (default: True)
        verbose (bool): Prints the scan_type, modality, and search terms used (e.g. func - bold - rest - ['rest', 'FFE'])
    
    
    Returns: 
        None
    '''
    
    mod_found = False

    converted_files = list()
    
    # Check file type
    if 'dcm' in file:
        if not cdm.is_valid_dcm(file,verbose):
            sys.exit(f"Invalid DICOM file. Please check {file}")
    
    for key,item in search_dict.items():
        for dict_key,dict_item in search_dict[key].items():
            if isinstance(dict_item,list):
                if utils.list_in_substr(dict_item,file):
                    mod_found = True
                    if verbose:
                        print(f"{key} - {dict_key}: {dict_item}")
                    scan_type = key
                    scan = dict_key
                    [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type)
                    if scan_type.lower() == 'dwi':
                        converted_files = csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                    elif scan_type.lower() == 'fmap':
                        converted_files = csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                    else:
                        converted_files = csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
                    if mod_found:
                        break
            elif isinstance(dict_item,dict):
                tmp_dict = search_dict[key]
                for d_key,d_item in tmp_dict[dict_key].items():
                    if utils.list_in_substr(d_item,file):
                        mod_found = True
                        if verbose:
                            print(f"{key} - {dict_key} - {d_key}: {d_item}")
                        scan_type = key
                        scan = dict_key
                        task = d_key
                        [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type,task=task)
                        if scan_type.lower() == 'func':
                            converted_files = csn.data_to_bids_func(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,task=task,meta_dict_com=com_param_dict,meta_dict_func=scan_param_dict,ses=ses,scan_type=scan_type)
                        elif scan_type.lower() == 'dwi':
                            converted_files = csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                        elif scan_type.lower() == 'fmap':
                            converted_files = csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                        else:
                            converted_files = csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
                        if mod_found:
                            break
                        
    if not mod_found:
        converted_files = get_scan_tech(bids_out_dir=bids_out_dir, sub=sub, file=file, search_dict=search_dict, meta_dict=dict(), ses=ses, keep_unknown=keep_unknown, verbose=verbose)
    
    return converted_files

def batch_convert(bids_out_dir,sub,file_list, search_dict, meta_dict=dict(), ses=1, keep_unknown=True,verbose=False):
    '''
    Batch conversion function for image files.
    
    Note: This function is still undergoing active development.

    Arguments:
        bids_out_dir (string): Output BIDS directory
        sub (int or string): Subject ID
        file_list (list): List of image files with absolute paths
        search_dict (dict): Nested dictionary from the 'read_config' function
        meta_dict (dict): Nested metadata dictionary
        ses (int or string): Session ID
        keep_unknown (bool): Convert modalities/scans which cannot be identified (default: True)
        verbose (bool): Prints the scan_type, modality, and search terms used (e.g. func - bold - rest - ['rest', 'FFE'])

    Returns: 
        None
    '''

    converted_files = list()
    
    for file in file_list:
        try:
            converted_files = convert_modality(bids_out_dir=bids_out_dir, sub=sub, file=file, search_dict=search_dict, meta_dict=meta_dict, ses=ses, keep_unknown=keep_unknown, verbose=verbose)
        except SystemExit:
            pass
    
    return converted_files

if __name__ == "__main__":

    # Info
    v_txt = os.path.join(os.path.dirname(__file__),'..','version.txt')
    version = utils.file_to_screen(v_txt)

    # Argument Parser
    parser = argparse.ArgumentParser(
        description=f'Performs conversion of source DICOM, PAR REC, and Nifti data to BIDS directory layout.\t\n\n convert_source v{version}\n\n')

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
                            metavar="Output_BIDS_Directory",
                            required=True,
                            help="BIDS output directory. This directory does not need to exist at runtime. The resulting directory will be populated with BIDS named and structured data.")
    reqoptions.add_argument('-d', '-data', '--data',
                            type=str,
                            dest="data_dir",
                            metavar="data_directory",
                            required=True,
                            help="Parent directory that contains that subuject's unconverted source data. This directory can contain either all the PAR REC files, or all the directories of the DICOM files. NOTE: filepaths with spaces either need to replaced with underscores or placed in quotes. NOTE: The PAR REC directory is rename PAR_REC automaticaly.")
    reqoptions.add_argument('-c', '-config', '--config',
                            type=str,
                            dest="conf",
                            metavar="config.yml",
                            required=True,
                            help="YAML configuruation file that contains modality search, parameters, metadata, and exclusion list.")
    reqoptions.add_argument('-f', '-file', '--file-type',
                            type=str,
                            dest="conv",
                            metavar="file_type",
                            required=True,
                            help="File type that is to be used with the converter. Acceptable choices include: DCM, PAR, or, NII.")

    # Optional Arguments
    optoptions = parser.add_argument_group('Optional arguments')
    optoptions.add_argument('-ses', '--ses',
                            type=str,
                            dest="ses",
                            metavar="session",
                            required=False,
                            default=1,
                            help="Session label for the acquired source data. [default: 1]")
    optoptions.add_argument('-k', '-keep', '--keep-unknown',
                            dest="keep_unknown",
                            required=False,
                            default=True,
                            action="store_true",
                            help="Keep or remove unknown modalities [default: True].")
    optoptions.add_argument('-v', '-verbose', '--verbose',
                            dest="verbose",
                            required=False,
                            default=False,
                            action="store_true",
                            help="Prints additional information to screen. [default: False]")
    optoptions.add_argument('-version', '--version',
                            dest="vers",
                            required=False,
                            default=False,
                            action="store_true",
                            help=f"Prints version to screen and exits. convert_source v{version}")

    args = parser.parse_args()

    # Print help message in the case
    # of no arguments
    try:
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            parser.print_help()

    # version flag
    if args.vers:
        print("")
        print(f"convert_source v{version}")
        print("")
        sys.exit()

    # Verbose flag
    if args.verbose:
        args.verbose = True

    # Convert Source Data Files
    if args.conv.upper() == 'PAR':
        file_ext = "PAR"
    elif args.conv.upper() == 'DCM':
        file_ext = "dcm"
    elif args.conv.upper() == 'NII':
        file_ext = "nii"
    else:
        print(
            "Option not recognized. Please use the \'--fileType\' option with either \'PAR\' or \'DCM\' as specified.")

    # Read config file
    [search_dict, exclude_list, meta_dict] = read_config(config_file=args.conf, verbose=args.verbose)

    # Create file list
    file_list_all = create_file_list(data_dir=args.data_dir,file_ext=file_ext)
    file_list = file_exclude(file_list_all, data_dir=args.data_dir, exclusion_list=exclude_list, verbose=args.verbose)

    # Batch convert files in file list
    batch_convert(bids_out_dir=args.out_bids,
                  sub=args.sub,
                  file_list=file_list,
                  search_dict=search_dict,
                  meta_dict=meta_dict,
                  ses=args.ses,
                  keep_unknown=args.keep_unknown,
                  verbose=args.verbose)

    print(f"Completed sub-{args.sub}")