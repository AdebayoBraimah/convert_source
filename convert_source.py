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
import pydicom
import json
import re
import os
import sys
import shutil
import glob
import random
import subprocess
import pathlib
import yaml
import nibabel as nib
import gzip
import pandas as pd
import numpy as np
import platform
import multiprocessing

# Import third party packages and modules
# import ...

# Define functions
def read_config(config_file, verbose = False):
    '''
    Reads configuration file and creates a dictionary of search terms for 
    certain modalities provided that BIDS modalities are used as keys. If
    exclusions are provided (via the key 'exclude') then an exclusion list is 
    created. Otherwise, 'exclusion_list' is returned as an empty list. If 
    additional settings are specified, they should be done so via the key
    'metadata' to enable writing of additional metadata. Otherwise, an 
    empty dictionary is returned.
    
    Arguments:
        config_file (string): file path to yaml configuration file.
        verbose (boolean): Prints additional information to screen.
    
    Returns: 
        data_map (dict): Nested dictionary of search terms for BIDS modalities
        exclusion_list (list): List of exclusion terms
        meta_dict (dict): Nested dictionary of metadata terms to write to JSON file(s)
    '''
    
    with open(config_file) as file:
        data_map = yaml.safe_load(file)
        if verbose:
            print("Initialized parameters from configuration file")
        
    if any("exclude" in data_map for element in data_map):
        if verbose:
            print("exclusion option implemented")
        exclusion_list = data_map["exclude"]
        del data_map["exclude"]
    else:
        if verbose:
            print("exclusion option not implemented")
        exclusion_list = list()
        
    if any("metadata" in data_map for element in data_map):
        if verbose:
            print("implementing additional settings for metadata")
        meta_dict = data_map["metadata"]
        del data_map["metadata"]
    else:
        if verbose:
            print("no metadata settings")
        meta_dict = dict()
        
    return data_map,exclusion_list,meta_dict

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
        file_list = sorted(get_dcm_files(data_dir), key=order_key, reverse=False)
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
            exclusion_set.update(f_names_set)
            
        currated_set = file_set.difference(exclusion_set)

    currated_list = list(currated_set)
    
    return currated_list

def str_in_substr(sub_str_,str_):
    '''
    DEPRECATED: Should only be used if config_file uses comma separated
        lists to denote search terms.
    
    Searches a (longer) string using a comma separated string 
    consisting of substrings. Returns 'True' or 'False' if any part
    of the substring is found within the larger string.
    
    Example:
        str_in_substr('T1,TFE','sub_T1_image_file') would return True.
        str_in_substr('T2,TSE','sub_T1_image_file') would return False.
    
    Arguments:
        sub_str_ (string): Substring used for matching.
        str_ (string): Larger string to be searched for matches within substring.
    
    Returns: 
        bool_var (bool): Boolean - True or False
    '''
    
    bool_var = False
    
    for word in sub_str_.split(","):
        if any(word in str_ for element in str_):
            bool_var = True
            
    return bool_var

def list_in_substr(list_,str_):
    '''
    Searches a string using a list that contains substrings. 
    Returns 'True' or 'False' if any elements of the list are 
    found within the string.
    
    Example:
        list_in_substr('['T1','TFE']','sub_T1_image_file') would return True.
        list_in_substr('['T2','TSE']','sub_T1_image_file') would return False.
    
    Arguments:
        list_ (string): list containing strings used for matching.
        str_ (string): Larger string to be searched for matches within substring.
    
    Returns: 
        bool_var (bool): Boolean - True or False
    '''
    
    bool_var = False
    
    for word in list_:
        if any(word.lower() in str_.lower() for element in str_.lower()):
            bool_var = True
            
    return bool_var

def get_scan_tech(search_dict, file, json_file=""):
    '''
    Searches DICOM or PAR file header for scan technique/MR modality used in accordance with the search terms provided
    by the nested dictionary.
    
    Note: This function is still undergoing active development.
    
    Arguments:
        search_dict (dict): Nested dictionary from the 'read_config' function
        dcm_file (string): Source image filename with absolute filepath
    
    Returns: 
        None
    '''
    
    # Check file extension in file
    # Perform Scanning Techniqe Search
    if '.dcm' in file.lower():
        get_dcm_scan_tech(search_dict,file)
    elif '.PAR' in file.upper():
        get_par_scan_tech(search_dict,file)
    else:
        print("unknown modality")
        
    return None

def convert_modality(file, search_dict, verbose=False):
    '''
    Converts an image file and extracts information from the filename (such as the modality). 
    
    Note: This function is still undergoing active development.
    Note: Add support for extra dictionaries
    
    Arguments:
        search_dict (dict): Nested dictionary from the 'read_config' function
        file (string): Filename with absolute filepath
        verbose (boolean): Enable verbosity
    
    Returns: 
        None
    '''
    
    mod_found = False
    
    # Check file type
    if 'nii' in file:
        file_ext = "nii"
        file_ext = f".{file_ext.lower()}"
    elif 'dcm' in file:
        file_ext = "dcm"
        file_ext = f".{file_ext.lower()}"
        if not is_valid_dcm(file,verbose):
            sys.exit(f"Invalid DICOM file. Please check {file}")
    
    for key,item in search_dict.items():
        for dict_key,dict_item in search_dict[key].items():
            if isinstance(dict_item,list):
                if list_in_substr(dict_item,file):
                    mod_found = True
                    if verbose:
                        print(f"{key} - {dict_key}: {dict_item}")
                    scan_type = key
                    scan = dict_key
                    if scan_type.lower() == 'dwi':
                        data_to_bids_dwi(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_dwi="",ses="",scan_type=scan_type)
                    elif scan_type.lower() == 'fmap':
                        data_to_bids_fmap(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_fmap="",ses="",scan_type=scan_type)
                    else:
                        data_to_bids_anat(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_anat="",ses="",scan_type=scan_type)
                    if mod_found:
                        break
            elif isinstance(dict_item,dict):
                tmp_dict = search_dict[key]
                for d_key,d_item in tmp_dict[dict_key].items():
                    if list_in_substr(d_item,file):
                        mod_found = True
                        if verbose:
                            print(f"{key} - {dict_key} - {d_key}: {d_item}")
                        scan_type = key
                        scan = dict_key
                        task = d_key
                        if scan_type.lower() == 'func':
                            data_to_bids_func(bids_out_dir,file,sub,scan,task="",meta_dict_com,meta_dict_func="",ses="",scan_type=scan_type)
                        elif scan_type.lower() == 'dwi':
                            data_to_bids_dwi(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_dwi="",ses="",scan_type=scan_type)
                        elif scan_type.lower() == 'fmap':
                            data_to_bids_fmap(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_fmap="",ses="",scan_type=scan_type)
                        else:
                            data_to_bids_anat(bids_out_dir,file,sub,scan,meta_dict_com,meta_dict_anat="",ses="",scan_type=scan_type)
                        if mod_found:
                            break
                        
    if not mod_found:
        get_scan_tech(search_dict,file)
    
    return None

def batch_convert(file_list, dictionary, verbose=False):
    '''
    Batch conversion function for image files. 
    
    Note: This function is still undergoing active development.
    
    Arguments:
        file_list (list): List of filenames with absolute filepaths
        dictionary (dict): Nested dictionary from the 'read_config' function
        verbose (boolean): Enable verbosity
    
    Returns: 
        None
    '''
    
    for file in file_list:
        try:
            convert_modality(dictionary,file,verbose)
        except SystemExit:
            pass
    
    return None

def get_data_params(file,json_file="", bval_file=""):
    '''
    Creates a dictionary of key mapped parameter items that are often not written to the BIDS JSON sidecar
    when converting Philips DICOM and PAR REC files.
    
    Arguments:
        file (string): Absolute filepath to raw image data file (DICOM or PAR REC)
        json_file (string, optional): Corresponding JSON sidecare file
        bval_file (string, optional): Corresponding bval file for DWI acquisitions
    
    Returns:
        info (dict): Dictionary of key mapped items/values
    '''
    
    # Create empty dictionary
    tmp_dict = dict()
    
    # Check and write bvalue(s) to file
    if bval_file:
        bval_list = get_bvals(bval_file)
        tmp_dict.update({"bval":bval_list})
    
    # Check file type
    if '.dcm' in file.lower():
        red_fact = get_red_fact(file)
        mb = get_mb(file)
        scan_time = get_scan_time(file)
        [eff_echo_sp, tot_read_time]  = calc_read_time(file,json_file)
        source_format = "DICOM"
        tmp_dict.update({"ParallelReductionFactorInPlane": red_fact,
                         "MultibandAccelerationFactor": mb,
                         "EffectiveEchoSpacing": eff_echo_sp,
                         "TotalReadoutTime": tot_read_time,
                         "AcquisitionDuration": scan_time,
                         "SourceDataFormat": source_format})
    elif 'PAR' in file.upper():
        wfs = get_wfs(file)
        red_fact = get_red_fact(file)
        mb = get_mb(file)
        scan_time = get_scan_time(file)
        etl = get_etl(file)
        [eff_echo_sp, tot_read_time]  = calc_read_time(file,json_file)
        source_format = "PAR REC"
        tmp_dict.update({"WaterFatShift": wfs,
                         "ParallelAcquisitionTechnique": 'SENSE',
                         "ParallelReductionFactorInPlane": red_fact,
                         "MultibandAccelerationFactor": mb,
                         "EffectiveEchoSpacing": eff_echo_sp,
                         "TotalReadoutTime": tot_read_time,
                         "AcquisitionDuration": scan_time,
                         "EchoTrainLength": etl,
                         "SourceDataFormat": source_format})
    elif 'nii' in file.lower():
        tr = get_nii_tr(file)
        source_format = "NIFTI"
        tmp_dict.update({"RepetitionTime": tr,
                         "SourceDataFormat": source_format})
    else:
        pass
        
    info = dict()
    info.update(tmp_dict)
    
    return info

def get_metadata(dictionary,scan_type="",task=""):
    '''
    Reads the metadata dictionary and looks for keywords to indicate what metadata should be written to which
    dictionary. For example, the keyword 'common' is used to indicate the common information for the imaging
    protocol and may contain information such as: field strength, phase encoding direction, institution name, etc.
    Additional keywords that are BIDS sub-directories names (e.g. anat, func, dwi) will return an additional
    dictionary which contains metadata specific for those modalities. Func also has additional keywords based on
    the task specified.
    
    Arguments:
        dictionary (dict): Nest dictionary of key mapped items from the 'read_config' function
        scan_type (string): BIDS scan type (e.g. anat, func, dwi, etc., default="")
        task (string): Task name to search in the key mapped dictionary
        
    Returns: 
        com_param_dict (dict): Common parameters dictionary
        scan_param_dict (dict): Scan/modality type parameters dictionary
    '''
    
    # Create empty dictionaries
    com_param_dict = dict()
    scan_param_dict = dict()
    scan_task_dict = dict()
    
    # Iterate through, looking for key words (e.g. common and scan_type)
    for key,item in dictionary.items():
        if key.lower() in 'common':
            com_param_dict = dictionary[key]

        if key.lower() in scan_type:
            scan_param_dict = dictionary[key]
            if task.lower() in scan_param_dict:
                for dict_key,dict_item in scan_param_dict.items():
                    if task.lower() in dict_key:
                        scan_task_dict = scan_param_dict[dict_key]
                        
        if len(scan_task_dict) != 0:
            scan_param_dict = scan_task_dict
    
    return com_param_dict, scan_param_dict 
