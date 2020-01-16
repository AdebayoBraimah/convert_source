# -*- coding: utf-8 -*-
'''
NifTi specific functions for convert_source. Primarily intended for renaming NifTi to be BIDS compliant.
'''

# Import packages and modules
import pydicom
import json
import re
import os
import sys
import subprocess
import nibabel as nib
import gzip
import numpy as np
import platform

# define functions

def get_nii_tr(nii_file):
    '''
    Reads the NifTi file header and returns the repetition time (TR, sec) as a value if it is not zero, otherwise this 
    function returns the string 'unknown'.
    
    Arguments:
        nii_file (string): NifTi image filename with absolute filepath
        
    Returns: 
        tr (float or string): Repetition time (TR, sec), if not zero, otherwise 'unknown' is returned.
    '''
    
    # Load nifti file
    img = nib.load(nii_file)
    
    # Store nifti image TR
    tr = float(img.header['pixdim'][4])
    
    # Check if TR is likely
    if tr != 0:
        pass
    else:
        tr = "unknown"
    
    return tr

