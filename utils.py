# -*- coding: utf-8 -*-
'''
Utility functions for convert_source.
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

# Define functions

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

def get_echo(json_file):
  '''
  Reads the echo time (TE) from the NifTi JSON sidecar and returns it.

  Arguments:
    json_file (string): Absolute path to JSON sidecar

  Returns:
    echo (float): Returns the echo time as a float.
  '''

  with open(json_file, "r") as read_file:
    data = json.load(read_file)

  echo = data.get("EchoTime")

  return echo

def get_num_runs(out_dir,scan,ses="",task="",acq="",ce="",dirs="",rec="",echo=""):
  '''
  Determines run number of a scan (e.g. T1w, T2w, bold, dwi etc.) in an output directory by globbing the 
  directory for the number of NifTis of the same scan.

  Arguments (required):
    out_dir (string): Absolute path to output directory
    scan (string): Modality (e.g. T1w, T2w, bold, dwi, etc.)

  Arguments (optional):
    ses (string): Session ID
    task (string): Task ID
    acq (string): Acquisition ID
    ce (string): Contrast Enhanced ID
    dirs (string): Directions ID string
    rec (string): Reconstruction algorithm string
    echo (int or string): Echo number from multi-echo functional scan

  Returns:
    run_num (int): Returns the run number for the specific scan
  '''

  runs = os.path.join(out_dir, f"*{ses}*{task}*{acq}*{ce}*{dirs}*{rec}*{echo}*{scan}*.nii*")
  run_num = len(glob.glob(runs))
  run_num = run_num + 1

  return run_num

def file_parts(file):
  '''
  Divides file with file path into: path, filename, extension.
  
  Arguments:
    file (string): File with absolute filepath
      
  Returns: 
    path (string): Path of input file
    filename (string): Filename of input file, without the extension
    ext (string): Extension of input file
  '''
  
  [path, file_with_ext] = os.path.split(file)
  [filename,ext] = os.path.splitext(file_with_ext)
  
  path = str(path)
  filename = str(filename)
  ext = str(ext)
  
  return path,filename,ext

def gzip_file(file,rm_orig=True):
  '''
  Gzips file.
  
  Arguments:
    file (string): Input file
    rm_orig (boolean): If true (default), removes original file
      
  Returns: 
    out_file (string): Gzipped file
  '''
  
  # Define tempory file for I/O buffer stream
  tmp_file = file
  path,f_name_,ext_ = file_parts(tmp_file)
  f_name = f_name_ + ext_ + ".gz"
  out_file = os.path.join(path,f_name)
  
  # Gzip file
  with open(file,"rb") as in_file:
    data = in_file.read(); in_file.close()
    with gzip.GzipFile(out_file,"wb") as tmp_out:
      tmp_out.write(data)
      tmp_out.close()
          
  if rm_orig:
    os.remove(file)
          
  return out_file

def gunzip_file(file,rm_orig=True):
  '''
  Gunzips file.
  
  Arguments:
    file (string): Input file
    rm_orig (boolean): If true (default), removes original file
      
  Returns: 
    out_file (string): Gunzipped file
  '''
  
  # Define tempory file for I/O buffer stream
  tmp_file = file
  path,f_name_,ext_ = file_parts(tmp_file)
  f_name = f_name_ # + ext_[:-3]
  out_file = os.path.join(path,f_name)
  
  with gzip.GzipFile(file,"rb") as in_file:
    data = in_file.read(); in_file.close()
    with open(out_file,"wb") as tmp_out:
      tmp_out.write(data)
      tmp_out.close()
          
  if rm_orig:
    os.remove(file)
  
  return out_file

def update_json(json_file,dictionary):
  '''
  Updates JavaScript Object Notation (JSON) file. If the file does not exist, it is created once
  this function is invoked. If the JSON file contains text/fields, then the contents are stored as
  a (nested) dictionary and then updated with the new dictionary. The updated dictionary is then 
  written to the JSON file.
  
  Arguments:
    json_file (string): Input file
    dictionary (dict): Dictionary of key mapped items to write to JSON file
      
  Returns: 
    json_file (string): Updated JSON file
  '''
  
  # Check if JSON file exists, if not, then create JSON file
  if not os.path.exists(json_file):
    with open(json_file,"w"): pass
      
  # Read JSON file
  # Try-Except statement has empty exception as JSONDecodeError is not a valid exception to pass, 
  # thus throwing a name error
  try:
    with open(json_file) as file:
      data_orig = json.load(file)
  except:
    pass
    data_orig = dict()
      
  # Update original data from JSON file
  data_orig.update(dictionary)
  
  # Write updated JSON file
  with open(json_file,"w") as file:
    json.dump(data_orig,file,indent=4)
      
  return json_file

def dict_multi_update(dictionary,**kwargs):
  '''
  Updates a dictionary multiple times depending on the number key word mapped pairs that are provided and 
  returns a separate updated dictionary. The dictionary passed as an argument must exist prior to this 
  function being invoked.
  
  Example usage:
  
    new_dict = dict_multi_update(old_dict,
                                Manufacturer="Philips",
                                ManufacturersModelName="Ingenia",
                                MagneticFieldStrength=3,
                                InstitutionName="CCHMC")
  
  Arguments:
    dictionary (dict): Dictionary of key mapped items to write to JSON file
    **kwargs (string, key,value pairs): key=value pairs
      
  Returns: 
    new_dict (dict): New updated dictionary
  '''
  
  # Create new dictionary
  new_dict = dictionary.copy()
  
  for key,item in kwargs.items():
    tmp_dict = {key:item}
    new_dict.update(tmp_dict)
      
  return new_dict

def get_bvals(bval_file):
  '''
  Reads the bvals from the (FSL-style) bvalue file and returns a list of unique non-zero bvalues
  
  Arguments:
    bval_file (string): Absolute filepath to bval (.bval) file
      
  Returns: 
    bvals_list (list): List of unique, non-zero bvalues.
  '''
  
  vals = np.loadtxt(bval_file)
  vals_nonzero = vals[vals.astype(bool)]
  bvals_list = list(np.unique(vals_nonzero))
  
  return bvals_list

def convert_image_data(file,basename,out_dir,cprss_lvl=6,bids=True,anon_bids=True,gzip=True,comment=True,adjacent=False,
  dir_search=5,nrrd=False,ignore_2D=True,merge_2D=True,text=False,progress=False,verbose=False,write_conflicts="suffix",
  crop_3D=False,lossless=False,big_endian="optimal",xml=False):
  '''
  Converts raw image data (DICOM, PAR REC, or Bruker) to NifTi (or NRRD) using dcm2niix.
  This is a wrapper function for dcm2niix (v1.0.20190902+). This wrapper functions has no returns, 
  however output files are generated in a specified directory that must exist prior to the 
  invokation of this function.
  
  Note: Most of the defaults for dcm2niix have been preserved aside from those starred (*) in the
  (optional) arguments section, in order to be BIDS compliant.

  Arguments (Required):
    file (string): Absolute path to raw image data file
    basename (string): Output file(s) basename
    out_dir (string): Absolute path to output directory (must exist at runtime)

  Arguments (Optional):
    cprss_lvl (int): Compression level [1 - 9] - 1 is fastest, 9 is smallest (default: 6)
    bids (bool): BIDS (JSON) sidecar (default: True) * 
    anon_bids (bool): Anonymize BIDS (default: True) * 
    gzip (bool): Gzip compress images (default: True) *
    comment (bool): Image comment(s) stored in NifTi header (default: True) *
    adjacent (bool): Assumes adjacent DICOMs/Image data (images from same series always in same folder) for faster conversion (default: False)
    dir_search (int): Directory search depth (default: 5)
    nrrd (bool): Export as NRRD instead of NifTi, not recommended (default: False)
    ignore_2D (bool): Ignore derived, localizer and 2D images (default: True)
    merge_2D (bool): Merge 2D slices from same series regardless of echo, exposure, etc. (default: True)
    text (bool): Text notes includes private patient details in separate text file (default: False)
    progress (bool): Report progress, slicer format progress information (default: False)
    verbose (bool): Enable verbosity (default: False)
    write_conflicts (string): Write behavior for name conflicts:
      - 'suffix' = Add suffix to name conflict (default)
      - 'overwrite' = Overwrite name conflict
      - 'skip' = Skip name conflict
    crop_3D (bool): crop 3D acquisitions (default: False)
    lossless (bool): Losslessly scale 16-bit integers to use dynamic range (default: False)
    big_endian (string): Byte order:
      - 'optimal' or 'native' = optimal/native byte order (default)
      - 'little-end' = little endian
      - 'big-end' = big endian
    xml (bool): Slicer format features (default: False)
      
      Returns:
        None
  '''

  # Empty list
  conv_cmd = list()

  # Get OS platform
  if platform.system().lower() == 'windows':
    conv_cmd.append("dcm2niix.exe")
  else:
    conv_cmd.append("dcm2niix")

  # Boolean True/False options arrays
  bool_opts = [bids, anon_bids, gzip, comment, adjacent, nrrd, ignore_2D, merge_2D, text, verbose, lossless, progress, xml]
  bool_vars = ["-b", "-ba", "-z", "-c", "-a", "-e", "-i", "-m", "-t", "-v", "-l", "--progress", "--xml"]

  # Initial option(s)
  if cprss_lvl:
    conv_cmd.append(f"-{cprss_lvl}")

  # Keyword option(s)
  if write_conflicts.lower() == "suffix":
    conv_cmd.append("-w")
    conv_cmd.append("2")
  elif write_conflicts.lower() == "overwrite":
    conv_cmd.append("-w")
    conv_cmd.append("1")
  elif write_conflicts.lower() == "skip":
    conv_cmd.append("-w")
    conv_cmd.append("0")

  if big_endian.lower() == "optimal" or big_endian.lower() == "native":
    conv_cmd.append("--big_endian")
    conv_cmd.append("o")
  elif big_endian.lower() == "little-end":
    conv_cmd.append("--big_endian")
    conv_cmd.append("n")
  elif big_endian.lower() == "big-end":
    conv_cmd.append("--big_endian")
    conv_cmd.append("y")


  for idx,var in enumerate(bool_opts):
    if var:
      conv_cmd.append(bool_vars[idx])
      conv_cmd.append("y")

  # Required arguments
  # Filename
  conv_cmd.append("-f")
  conv_cmd.append(f"{basename}")

  # Output directory
  conv_cmd.append("-o")
  conv_cmd.append(f"{out_dir}")

  # Image file   
  conv_cmd.append(f"{file}")

  # System Call to dcm2niix (assumes dcm2niix is added to system path variable)
  subprocess.call(conv_cmd)