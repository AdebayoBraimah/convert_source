# -*- coding: utf-8 -*-
'''
PAR REC specific functions for convert_source. Primarily intended for converting and renaming PAR REC files to BIDS NifTi.
'''

# Import packages and modules
import json
import re
import os
import sys
import subprocess
import nibabel as nib
import gzip
import numpy as np
import platform

# Define functions

def get_par_scan_tech(dictionary, par_file):
    '''
    Searches PAR file header for scan technique/MR modality used in accordance with the search terms provided by the
    nested dictionary. A regular expression (regEx) search string is defined and searched for conventional PAR headers.
    
    Note: This function is still undergoing active development.
    
    Arguments:
        dictionary (dict): Nested dictionary from the 'read_config' function
        par_file (string): PAR filename with absolute filepath
    
    Returns: 
        None
    '''
    
    mod_found = False
    
    # Define regEx search string
    regexp = re.compile(r'.    Technique                          :  .*', re.M | re.I)
    
    # Open and search PAR header file
    with open(par_file) as f:
        for line in f:
            match_ = regexp.match(line)
            if match_:
                par_scan_tech_str = match_.group()
    
    # Search Scan Technique with search terms
    for key,item in dictionary.items():
        for dict_key,dict_item in dictionary[key].items():
            if isinstance(dict_item,list):
                if list_in_substr(dict_item,par_scan_tech_str):
                    mod_found = True
                    print(f"{key} - {dict_key}: {dict_item}")
                    if mod_found:
                        break
            elif isinstance(dict_item,dict):
                tmp_dict = dictionary[key]
                for d_key,d_item in tmp_dict[dict_key].items():
                    if list_in_substr(d_item,par_scan_tech_str):
                        mod_found = True
                        print(f"{key} - {dict_key} - {d_key}: {d_item}")
                        if mod_found:
                            break
                            
        if mod_found:
            break
            
    if not mod_found:
        print("unknown modality")
    
    return None

  