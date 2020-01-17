# -*- coding: utf-8 -*-
'''
DICOM specific functions for convert_source. Primarily intended for converting and renaming DICOM files to BIDS NifTi.
'''

# Import packages and modules
import pydicom
import re
import os
import glob

# Import third party packages and modules
import utils
import convert_source_nii as csn

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

def get_red_fact(dcm_file):
    '''
    Extracts parallel reduction factor in-plane value (GRAPPA/SENSE) from file description in the DICOM 
    header for Philips MR scanners. This reduction factor is assumed to be 1 if a value cannot be found 
    from witin the DICOM header.
    
    Arguments:
        dcm_file (string): Absolute filepath to DICOM file
        
    Returns:
        red_fact (float): parallel reduction factor in-plane value (e.g. SENSE factor)
    '''

    # Load dicom data
    ds = pydicom.dcmread(dcm_file)
    red_fact = ""
    
    # Get Info
    try:
        red_fact = ds[0x0018,0x9069]
    except KeyError:
        pass
    
    # Get image descriptor
    if not red_fact:
        line = ds.SeriesDescription
        match = re.search(r'SENSE .*?([0-9.-]+)', line, re.M | re.I)
        if match:
            red_fact = match.group(1)
            red_fact = float(red_fact)
        else:
            red_fact = float(1)

    return red_fact

def get_mb(dcm_file):
    '''
    Extracts multi-band acceleration factor from file description in the DICOM header for philips MR scanners.
    
    N.B.: This is done via a regEx search as no DICOM tag stores this information explicitly.
    
    Arguments:
        dcm_file (string): Absolute filepath to DICOM file
        
    Returns:
        mb (int): multi-band acceleration factor
    '''

    # Initialize mb to 1
    mb = 1

    # Load dicom data
    ds = pydicom.dcmread(dcm_file)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'MB.*?([0-9.-]+)', line, re.M | re.I)
    if match:
        mb = match.group(1)
        mb = int(mb)

    return mb

def get_dcm_scan_tech(bids_out_dir, sub, dcm_file, search_dict, meta_dict={}, ses=1, keep_unknown=True, verbose=False):
    '''
    Searches DICOM file header for scan technique/MR modality used in accordance with the search terms provided by the
    nested dictionary. The DICOM header field searched is a Philips DICOM private tag (2001,1020) [Scanning Technique 
    Description MR]. In the case that field does not match, is empty, or does not exist, then more common DICOM tags
    are searched - and they include: Series Description, Protocol Name, and Image Type.
    
    Note: This function is still undergoing active development.
    
    Arguments:
        bids_out_dir (string): Output BIDS directory
        sub (int or string): Subject ID
        dcm_file (string): DICOM filename with absolute filepath
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
    
    mod_found = False
    
    # Load DICOM data and read header
    ds = pydicom.dcmread(dcm_file)
    
    # Search DICOM header for Scan Technique used
    dcm_scan_tech_str = str(ds[0x2001,0x1020])
    
    for key,item in search_dict.items():
        for dict_key,dict_item in search_dict[key].items():
            if isinstance(dict_item,list):
                if utils.list_in_substr(dict_item,dcm_scan_tech_str):
                    mod_found = True
                    if verbose:
                        print(f"{key} - {dict_key}: {dict_item}")
                    scan_type = key
                    scan = dict_key
                    [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type)
                    if scan_type.lower() == 'dwi':
                        csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                    elif scan_type.lower() == 'fmap':
                        csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                    else:
                        csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
                    if mod_found:
                        break
            elif isinstance(dict_item,dict):
                tmp_dict = search_dict[key]
                for d_key,d_item in tmp_dict[dict_key].items():
                    if utils.list_in_substr(d_item,dcm_scan_tech_str):
                        mod_found = True
                        if verbose:
                            print(f"{key} - {dict_key} - {d_key}: {d_item}")
                        scan_type = key
                        scan = dict_key
                        task = d_key
                        [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type,task=task)
                        if scan_type.lower() == 'func':
                            csn.data_to_bids_func(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,task=task,meta_dict_com=com_param_dict,meta_dict_func=scan_param_dict,ses=ses,scan_type=scan_type)
                        elif scan_type.lower() == 'dwi':
                            csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                        elif scan_type.lower() == 'fmap':
                            csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                        else:
                            csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
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
            
            for key,item in search_dict.items():
                for dict_key,dict_item in search_dict[key].items():
                    if isinstance(dict_item,list):
                        if utils.list_in_substr(dict_item,dcm_scan_tech_str):
                            mod_found = True
                            if verbose:
                                print(f"{key} - {dict_key}: {dict_item}")
                            scan_type = key
                            scan = dict_key
                            [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type)
                            if scan_type.lower() == 'dwi':
                                csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                            elif scan_type.lower() == 'fmap':
                                csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                            else:
                                csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
                            if mod_found:
                                break
                    elif isinstance(dict_item,dict):
                        tmp_dict = search_dict[key]
                        for d_key,d_item in tmp_dict[dict_key].items():
                            if utils.list_in_substr(d_item,dcm_scan_tech_str):
                                mod_found = True
                                if verbose:
                                    print(f"{key} - {dict_key} - {d_key}: {d_item}")
                                scan_type = key
                                scan = dict_key
                                task = d_key
                                [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type,task=task)
                                if scan_type.lower() == 'func':
                                    csn.data_to_bids_func(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,task=task,meta_dict_com=com_param_dict,meta_dict_func=scan_param_dict,ses=ses,scan_type=scan_type)
                                elif scan_type.lower() == 'dwi':
                                    csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
                                elif scan_type.lower() == 'fmap':
                                    csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
                                else:
                                    csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
                                if mod_found:
                                    break

            if mod_found:
                break
                
    if not mod_found:
        if verbose:
            print("unknown modality")
        if keep_unknown:
            scan_type = 'unknown_modality'
            scan = 'unknown'
            csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=dcm_file,sub=sub,scan=scan,meta_dict_com={},meta_dict_anat={},ses=ses,scan_type=scan_type)
        
    return None

