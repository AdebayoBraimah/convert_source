# -*- coding: utf-8 -*-
"""PAR REC specific functions for convert_source. Primarily intended for converting and renaming PAR REC files to BIDS NIFTI.

TODO:
    * Figure out a way to get EchoTimes from PAR header file(s).
        * Perhaps return as list if multi-echo
        * Return as list if multiple unique values exist.
        * Update csn function that updates dictionary.
"""

# Import packages and modules
import os
import re
import numpy as np
import pandas as pd
from typing import (
    List, 
    Dict, 
    Optional, 
    Union, 
    Tuple
)

from convert_source.cs_utils.fileio import TmpDir

# from convert_source.imgio import niio

# Define exception(s)
class PARfileReadError(Exception):
    pass

# Define function(s)
def get_etl(par_file: str) -> float:
    '''Gets EPI factor (Echo Train Length) from Philips' PAR Header.
    
    N.B.: This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Echo Train Length as float.
    '''
    par_file: str = os.path.abspath(par_file)
    regexp: re = re.compile(r'.    EPI factor        <0,1=no EPI>     :   .*?([0-9.-]+)')  # Search string for RegEx
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                etl = match.group(1)
                etl: int = int(etl)
    return etl

def get_wfs(par_file: str) -> float:
    '''Gets Water Fat Shift from Philips' PAR Header.
    
    N.B.: This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Water Fat Shift as a float.
    '''
    par_file: str = os.path.abspath(par_file)
    regexp: re = re.compile(
        r'.    Water Fat shift \[pixels\]           :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                wfs = match.group(1)
                wfs: float = float(wfs)
    return wfs

def get_red_fact(par_file: str) -> float:
    '''Extracts parallel reduction factor in-plane value (SENSE factor) from the file description in the PAR REC header 
    for Philips MR scanners. This reduction factor is assumed to be 1 if a value cannot be found from witin
    the PAR REC header.
    
    N.B.: This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Parallel reduction factor in-plane value (e.g. SENSE factor, as a float).
    '''
    
    # Read file
    par_file: str = os.path.abspath(par_file)
    red_fact: str = ""
    regexp: re = re.compile(r' SENSE *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                red_fact = match.group(1)
                red_fact: float = float(red_fact)
            else:
                red_fact: float = float(1)
    return red_fact

def get_mb(par_file: str) -> int:
    '''Extracts multi-band acceleration factor from from Philips' PAR Header.
    
    N.B.: This is done via a regEx search as the PAR header does not normally store this value.
    
    Arguments:
        par_file: Absolute filepath to PAR header file
        
    Returns:
        Multi-band acceleration factor (as an int).
    '''
    par_file: str = os.path.abspath(par_file)

    # Initialize mb to 1
    mb: int = 1
    
    regexp: re = re.compile(r' MB *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                mb = match.group(1)
                mb: int = int(mb)
    return mb

def get_scan_time(par_file: str) -> Union[float,str]:
    '''Gets the acquisition duration (scan time, in s) from the PAR header.
    
    N.B.: This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Acquisition duration (scan time, in s). If not in header, an empty string is returned.
    '''
    par_file: str = os.path.abspath(par_file)
    scan_time: str = ''
    regexp: re = re.compile(
        r'.    Scan Duration \[sec\]                :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scan_time = match.group(1)
                scan_time: float = float(scan_time)
    return scan_time

def get_echo_time(par_file: str,
                 tmp_dir: Optional[str] = None
                 ) -> float:
    '''Reads the echo time (TE, in ms) from a PAR header file.
    
    Usage example:
        >>> get_echo_time(par_file="File.PAR")
        88.0
        
    Arguments:
        par_file: PAR header file.
        tmp_dir: Path to temporary directory.
        
    Returns:
        Echo time as a float.
    '''
    
    # NOTE: Echo time is obtained from the PAR file header by reading in the PAR header file as a
    #   pandas dataframe, followed by saving the resulting dataframe as a M x N | N = 35. The echo times
    #   are stored in the resulting matrix (constructed from numpy as a numpy multi-dimensional array) in 
    #   row 16 (count starts at 0).
    
    if tmp_dir:
        pass
    else:
        tmp_dir: str = os.getcwd()
    
    par_file: str = os.path.abspath(par_file)
        
    df: pd.DataFrame = pd.read_csv(par_file,sep="\s+",skiprows=98)
    df: pd.DataFrame = df.dropna(axis=0)
    
    # use tmp_dir here
    with TmpDir(tmp_dir=tmp_dir,use_cwd=False) as tmp:
        tmp.mk_tmp_dir()
        with TmpDir.TmpFile(tmp_dir=tmp.tmp_dir,ext="txt") as f:
            df.to_csv(f.file,sep=",",header=False,index=False)
            mat = np.loadtxt(f.file,delimiter=",")
        tmp.rm_tmp_dir(rm_parent=False)
    
    if len(list(np.unique(mat[0:,16]))) > 1:
        raise PARfileReadError(f"Two or more unique echo times were found in {par_file}. Please check.")
    else:
        return float(np.unique(mat[0:,16]))

def get_flip_angle(par_file: str,
                   tmp_dir: Optional[str] = None
                  ) -> float:
    '''Reads the flip angle (in degrees) from a PAR header file.
    
    Usage example:
        >>> get_flip_angle(par_file="File.PAR")
        90.0
        
    Arguments:
        par_file: PAR header file.
        tmp_dir: Path to temporary directory.
        
    Returns:
        Flip angle as a float.
    '''
    
    # NOTE: Flip angle is obtained from the PAR file header by reading in the PAR header file as a
    #   pandas dataframe, followed by saving the resulting dataframe as a M x N | N = 35. The flip angles
    #   are stored in the resulting matrix (constructed from numpy as a numpy multi-dimensional array) in 
    #   row 21 (count starts at 0).
    
    if tmp_dir:
        pass
    else:
        tmp_dir: str = os.getcwd()
    
    par_file: str = os.path.abspath(par_file)
        
    df: pd.DataFrame = pd.read_csv(par_file,sep="\s+",skiprows=98)
    df: pd.DataFrame = df.dropna(axis=0)
    
    # use tmp_dir here
    with TmpDir(tmp_dir=tmp_dir,use_cwd=False) as tmp:
        tmp.mk_tmp_dir()
        with TmpDir.TmpFile(tmp_file="file.tmp.txt",tmp_dir=tmp.tmp_dir) as f:
            df.to_csv(f.file,sep=",",header=False,index=False)
            mat = np.loadtxt(f.file,delimiter=",")
        tmp.rm_tmp_dir(rm_parent=False)
    
    if len(list(np.unique(mat[0:,21]))) > 1:
        raise PARfileReadError(f"Two or more unique flip angles were found in {par_file}. Please check.")
    else:
        return float(np.unique(mat[0:,21]))

# def get_par_scan_tech(bids_out_dir, sub, par_file, search_dict, meta_dict={}, ses=1, keep_unknown=True, verbose=False):
#     '''
#     Searches PAR file header for scan technique/MR modality used in accordance with the search terms provided by the
#     nested dictionary. A regular expression (regEx) search string is defined and searched for conventional PAR headers.
    
#     Note: This function is still undergoing active development.

#     Arguments:
#         bids_out_dir (string): Output BIDS directory
#         sub (int or string): Subject ID
#         par_file (string): PAR filename with absolute filepath
#         search_dict (dict): Nested dictionary from the 'read_config' function
#         meta_dict (dict): Nested metadata dictionary
#         ses (int or string): Session ID
#         keep_unknown (bool): Convert modalities/scans which cannot be identified (default: True)
#         verbose (bool): Prints the scan_type, modality, and search terms used (e.g. func - bold - rest - ['rest', 'FFE'])
    
#     Returns: 
#         None
#     '''

#     if not meta_dict:
#         meta_dict = dict()
    
#     mod_found = False
    
#     # Define regEx search string
#     regexp = re.compile(r'.    Technique                          :  .*', re.M | re.I)
    
#     # Open and search PAR header file
#     with open(par_file) as f:
#         for line in f:
#             match_ = regexp.match(line)
#             if match_:
#                 par_scan_tech_str = match_.group()
    
#     # Search Scan Technique with search terms
#     for key,item in search_dict.items():
#         for dict_key,dict_item in search_dict[key].items():
#             if isinstance(dict_item,list):
#                 if utils.list_in_substr(dict_item,par_scan_tech_str):
#                     mod_found = True
#                     if verbose:
#                         print(f"{key} - {dict_key}: {dict_item}")
#                     scan_type = key
#                     scan = dict_key
#                     [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type)
#                     if scan_type.lower() == 'dwi':
#                         csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
#                     elif scan_type.lower() == 'fmap':
#                         csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
#                     else:
#                         csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
#                     if mod_found:
#                         break
#             elif isinstance(dict_item,dict):
#                 tmp_dict = search_dict[key]
#                 for d_key,d_item in tmp_dict[dict_key].items():
#                     if utils.list_in_substr(d_item,par_scan_tech_str):
#                         mod_found = True
#                         if verbose:
#                             print(f"{key} - {dict_key} - {d_key}: {d_item}")
#                         scan_type = key
#                         scan = dict_key
#                         task = d_key
#                         [com_param_dict, scan_param_dict] = utils.get_metadata(dictionary=meta_dict,scan_type=scan_type,task=task)
#                         if scan_type.lower() == 'func':
#                             csn.data_to_bids_func(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,task=task,meta_dict_com=com_param_dict,meta_dict_func=scan_param_dict,ses=ses,scan_type=scan_type)
#                         elif scan_type.lower() == 'dwi':
#                             csn.data_to_bids_dwi(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_dwi=scan_param_dict,ses=ses,scan_type=scan_type)
#                         elif scan_type.lower() == 'fmap':
#                             csn.data_to_bids_fmap(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_fmap=scan_param_dict,ses=ses,scan_type=scan_type)
#                         else:
#                             csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com=com_param_dict,meta_dict_anat=scan_param_dict,ses=ses,scan_type=scan_type)
#                         if mod_found:
#                             break
                            
#         if mod_found:
#             break
            
#     if not mod_found:
#         if verbose:
#             print("unknown modality")
#         if keep_unknown:
#             scan_type = 'unknown_modality'
#             scan = 'unknown'
#             csn.data_to_bids_anat(bids_out_dir=bids_out_dir,file=par_file,sub=sub,scan=scan,meta_dict_com={},meta_dict_anat={},ses=ses,scan_type=scan_type)
        
#     return None
