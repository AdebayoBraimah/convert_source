# -*- coding: utf-8 -*-
'''
DICOM specific functions for convert_source. Primarily intended for converting and renaming DICOM files to BIDS NifTi.
'''

# Import packages and modules
import pydicom
import json
import re
import os
import shutil
import glob
import random
import subprocess
import nibabel as nib

# Define functions

def get_scan_time(dcm_file):
    '''
    Reads the scan time from the DICOM header.

    Arguments:
        dcm_file (string): Absolute path to DICOM file

    Returns:
        scan_time (float or string): Returns acquisition duration (scan time) as a float if it exists, otherwise the string 'unknown' is returned
    '''

    # Load data
    ds = pydicom.dcmread(dcm_file)

    # Gets scan time
    try:
    scan_time = ds.AcquisitionDuration
    except AttributeError:
    pass
    scan_time = 'unknown'

    return scan_time

def get_dcm_files(dcm_dir):
    '''
    Creates a file list consisting of the first DICOM file in a parent DICOM directory. 
    A file list is then returned.

    Arguments:
        dcm_dir (string): Absolute path to parent DICOM data directory

    Returns: 
        dcm_files (list): List of DICOM filenames, complete with their absolute paths.
    '''

    # Create directory list
    dcm_dir = os.path.abspath(dcm_dir)
    parent_dcm_dir = os.path.join(dcm_dir,'*')
    dcm_dir_list = glob.glob(parent_dcm_dir, recursive=True)

    # Initilized dcm_file list
    dcm_files = list()

    # Iterate through files in the dicom directory list
    for dir_ in dcm_dir_list:
    # print(dir_)
    for root, dirs, files in os.walk(dir_):
        tmp_dcm_file = files[0] # only need the first dicom file
        tmp_dcm_dir = root
        tmp_file = os.path.join(tmp_dcm_dir, tmp_dcm_file)

        dcm_files.append(tmp_file)
        break

    return dcm_files

def is_valid_dcm(dcm_file, verbose=False):
    '''
    Checks for a valid DICOM file by inspecting the conversion type label in the DICOM file header.
    This field should be blank. If this label is populated, then it is likely a secondary capture image 
    and thus is not likely to contain meaningful image information.
    
    Arguments:
        dcm_file (string): DICOM filename with absolute filepath
        verbose (boolean): Enable verbosity
    
    Returns: 
        is_valid (boolean): True if DICOM file is not a secondary capture (or does not have text in the conversion type label field)
    '''
    
    # Read DICOM file header
    ds = pydicom.dcmread(dcm_file)
    
    # Invalid files include secondary image captures, and are not suitable for 
    # nifti conversion as they are often not converted and cause problems.
    # This string should be empty. If it is populated, then its likely a secondary capture.
    conv_type = ds.ConversionType
    
    if conv_type in '':
        is_valid = True
    else:
        is_valid = False
        if verbose:
            print(f"Please check Conversion Type (0008, 0064) in dicom header. The presented DICOM file is not a valid file: {dcm_file}.")
    
    return is_valid

def get_bwpppe(dcm_file):
    '''
    Reads the Bandwidth Per Pixel PhaseEncode value from a DICOM header. 
    
    Note: This DICOM field is usually left blank on Philips DICOM headers.
    
    Arguments:
        dcm_file (string): Absolute filepath to DICOM file
        
    Returns:
        bwpppe (float or string): Bandwidth Per Pixel PhaseEncode value
    '''
    
    # Load data
    ds = pydicom.dcmread(dcm_file)
    
    # Get relevant DICOM field
    try:
        val_str = str(ds[0x0019, 0x1028])
        val_list = val_str.split(" ")
        bwpppe = val_list[-1]
        bwpppe = float(bwpppe)
    except (AttributeError,KeyError):
        bwpppe = 'unknown'
        pass
    
    return bwpppe

def get_dcm_scan_tech(dictionary, dcm_file):
    '''
    Searches DICOM file header for scan technique/MR modality used in accordance with the search terms provided by the
    nested dictionary. The DICOM header field searched is a Philips DICOM private tag (2001,1020) [Scanning Technique 
    Description MR]. In the case that field does not match, is empty, or does not exist, then more common DICOM tags
    are searched - and they include: Series Description, Protocol Name, and Image Type.
    
    Note: This function is still undergoing active development.
    
    Arguments:
        dictionary (dict): Nested dictionary from the 'read_config' function
        dcm_file (string): DICOM filename with absolute filepath
    
    Returns: 
        None
    '''
    
    mod_found = False
    
    # Load DICOM data and read header
    ds = pydicom.dcmread(dcm_file)
    
    # Search DICOM header for Scan Technique used
    dcm_scan_tech_str = str(ds[0x2001,0x1020])
    
    for key,item in dictionary.items():
        for dict_key,dict_item in dictionary[key].items():
            if isinstance(dict_item,list):
                if list_in_substr(dict_item,dcm_scan_tech_str):
                    mod_found = True
                    print(f"{key} - {dict_key}: {dict_item}")
                    if mod_found:
                        break
            elif isinstance(dict_item,dict):
                tmp_dict = dictionary[key]
                for d_key,d_item in tmp_dict[dict_key].items():
                    if list_in_substr(d_item,dcm_scan_tech_str):
                        mod_found = True
                        print(f"{key} - {dict_key} - {d_key}: {d_item}")
                        if mod_found:
                            break
                            
        if mod_found:
            break
    
    # Secondary look in the case Private Field (2001, 1020) [Scanning Technique Description MR] is empty
    if not mod_found:
        # Define list of DICOM header fields
        dcm_fields = ['SeriesDescription', 'ImageType', 'ProtocolName']
        
        for dcm_field in dcm_fields:
            dcm_scan_tech_str = str(eval(f"ds.{dcm_field}")) # This makes me dangerously uncomfortable
            
            for key,item in dictionary.items():
                for dict_key,dict_item in dictionary[key].items():
                    if isinstance(dict_item,list):
                        if list_in_substr(dict_item,dcm_scan_tech_str):
                            mod_found = True
                            print(f"{key} - {dict_key}: {dict_item}")
                            if mod_found:
                                break
                    elif isinstance(dict_item,dict):
                        tmp_dict = dictionary[key]
                        for d_key,d_item in tmp_dict[dict_key].items():
                            if list_in_substr(d_item,dcm_scan_tech_str):
                                mod_found = True
                                print(f"{key} - {dict_key} - {d_key}: {d_item}")
                                if mod_found:
                                    break

            if mod_found:
                break
                
    if not mod_found:
        print("unknown modality")
        
    return None
