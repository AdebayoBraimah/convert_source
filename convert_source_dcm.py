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

def is_valid_mr(dcm_file, verbose=False):
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

