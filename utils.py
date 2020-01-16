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
    this function is invoked.
    
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

def convert_image_data(file,basename,out_dir,cprss_lvl=6,bids=True,
                       anon_bids=True,gzip=True,comment=True,
                       adjacent=False,dir_search=5,nrrd=False,
                       ignore_2D=True,merge_2D=True,text=False,
                       progress=False,verbose=False,
                       write_conflicts="suffix",crop_3D=False,
                       lossless=False,big_endian="optimal",xml=False):
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
        progress (bool): Report progress, slicer format progress information (default: True)
        verbose (bool): Enable verbosity (default: False)
        write_conflicts (string): Write behavior for name conflicts:
            - 'suffix' = Add suffix to name conflict (default)
            - 'overwrite' = Overwrite name conflict
            - 'skip' = Skip name conflict
        crop_3D (bool): crop 3D acquisitions (default: False)
        lossless (bool): Losslessly scale 16-bit integers to use dynamic range (default: True)
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

    # Required option(s)
    if basename:
        conv_cmd.append("-f")
        conv_cmd.append(f"{basename}")

    if basename:
        conv_cmd.append("-f")
        conv_cmd.append(f"{basename}")

    if out_dir:
        conv_cmd.append("-o")
        conv_cmd.append(f"{out_dir}")

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

    return None

def cp_file(file,work_dir="",work_name=""):
    '''
    Copies a file. Primarily intended for copying single file image data.
    
    Arguments:
        file (string): File path to source (image) file
        work_dir (string): Absolute path to working directory (must exist at runtime prior to invoakation of this function). If left empty, then the directory of the source file is used.
        work_name (string): Output name for (image) file. If left empty, the output name is the same as the source file.
        
    Returns:
        out_file (string): Absolute path to output file.
    '''
    
    [path, filename, ext] = file_parts(file)
    
    if work_dir == "":
        work_dir = path
    else:
        work_dir = os.path.abspath(work_dir)
        
    if work_name == "":
        work_name = filename
        
    out_file = os.path.join(work_dir,work_name + ext)
    
    shutil.copy(file,out_file)
    
    return out_file

def get_recon_mat(json_file):
    '''
    Reads ReconMatrixPE (reconstruction matrix phase encode) value from the JSON sidecar.
    
    Arguments:
        json_file (string): Absolute filepath to JSON file
        
    Returns:
        recon_mat (float or string): Recon Matrix PE value
    '''
    
    # Read JSON file
    # Try-Except statement has empty exception as JSONDecodeError is not a valid exception to pass, 
    # thus throwing a name error
    try:
        with open(json_file, "r") as read_file:
            data = json.load(read_file)
            recon_mat = data["ReconMatrixPE"]
    except:
        recon_mat = 'unknown'
        pass
    
    return recon_mat

def get_pix_band(json_file):
    '''
    Reads pixel bandwidth value from the JSON sidecar.
    
    Arguments:
        json_file (string): Absolute filepath to JSON file
        
    Returns:
        pix_band (float or string): Pixel bandwidth value
    '''
    
    # Read JSON file
    # Try-Except statement has empty exception as JSONDecodeError is not a valid exception to pass, 
    # thus throwing a name error
    try:
        with open(json_file, "r") as read_file:
            data = json.load(read_file)
            pix_band = data["PixelBandwidth"]
    except:
        pix_band = 'unknown'
        pass
    
    return pix_band

def calc_read_time(file, json_file=""):
    '''
    Calculates the effective echo spacing and total readout time provided several combinations of parameters.
    Several approaches and methods to calculating the effective echo spacing and total readout within this function
    differ and are dependent on the parameters found within the provided JSON sidecar. Currently, there a four 
    approaches for calculating the effective echo space (all with differing values) and two ways of calculating 
    the total readout time. It should also be noted that several of these approaches are vendor specific (e.g. at 
    the time of writing, 16 Jan 2019, the necessary information for approach 1 is only found in Siemens DICOM 
    headers - the necessary information for approach 2 is only possible if the data is stored in PAR REC format as the
    WaterFatShift is a private tag in the Philips DICOM header - approaches 3 and 4 are intended for Philips/GE DICOMs 
    as those values are anticipated to exist in their DICOM headers).
    
    The approaches are listed below:
    
    Approach 1 (BIDS method, Siemens):
        BWPPPE = BandwidthPerPixelPhaseEncode
        EffectiveEchoSpacing = 1/[BWPPPE * ReconMatrixPE]
        TotalReadoutTime = EffectiveEchoSpacing * (ReconMatrixPE - 1)
        
    Approach 2 (Philips method - PAR REC):
        EffectiveEchoSpacing = (((1000 * WaterFatShift)/(434.215 * (EchoTrainLength + 1)))/ParallelReductionFactorInPlane)
        TotalReadoutTime = 0.001 * EffectiveEchoSpacing * EchoTrainLength
    
    Approach 3 (Philips/GE method - DICOM):
        EffectiveEchoSpacing = ((1/(PixelBandwidth * EchoTrainLength)) * (EchoTrainLength - 1))
        TotalReadoutTime = EffectiveEchoSpacing * (EchoTrainLength - 1)
        
    Approach 4 (Philips/GE method - DICOM):
        EffectiveEchoSpacing = ((1/(PixelBandwidth * ReconMatrixPE)) * (ReconMatrixPE - 1))
        tot_read_time = EffectiveEchoSpacing * (ReconMatrixPE - 1)
        
        Note: EchoTrainLength is assumed to be equal to ReconMatrixPE for approaches 3 and 4, as these values are generally close.
    
    Arguments:
        file (string): Absolute filepath to raw image data file (DICOM or PAR REC)
        json_file (string, optional): Absolute filepath to JSON sidecare
        
    Returns:
        eff_echo_sp (float): Effective Echo Spacing
        tot_read_time (float): Total Readout Time
        
    References:
    Approach 1: https://github.com/bids-standard/bids-specification/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md
    Approach 2: https://osf.io/hks7x/ - page 7
    
    Approaches 3 and 4 were found thorugh trial and error and yielded similar, but not the same values as approaches 1 and 2.
    '''
    
    # check file extension
    if 'dcm' in file:
        calc_method = 'dcm'
    elif 'PAR' in file:
        calc_method = 'par'
        
    # Create empty string variables
    bwpppe = ''
    recon_mat = ''
    pix_band = ''
    wfs = ''
    etl = ''
    red_fact = ''
        
    if calc_method.lower() == 'dcm':
        bwpppe = get_bwpppe(file)
        if json_file:
            recon_mat = get_recon_mat(json_file)
            pix_band = get_pix_band(json_file)
            # set bandwidth per pixel to empty if unknown
            try:
                if bwpppe.lower() == 'unknown':
                    bwpppe = ''
            except AttributeError:
                pass
            # set pixel bandwidth to empty if unknown
            try:
                if pix_band.lower() == 'unknown':
                    pix_band = ''
            except AttributeError:
                pass
            etl = recon_mat
    elif calc_method.lower() == 'par':
        wfs = get_wfs(file)
        etl = get_etl(file)
        red_fact = get_red_fact(file)
        # set water fat shift to empty if unknown
        try:
            if wfs.lower() == 'unknown':
                wfs = ''
        except AttributeError:
            pass
        # set echo train length to empty if unknown
        try:
            if etl.lower() == 'unknown':
                etl = ''
        except AttributeError:
            pass
         # set parallel reduction factor to empty if unknown
        try:
            if red_fact.lower() == 'unknown':
                red_fact = ''
        except AttributeError:
            pass
    
    # Calculate effective echo spacing and total readout time
    if bwpppe and recon_mat:
        eff_echo_sp = 1/(bwpppe * recon_mat)
        tot_read_time = eff_echo_sp * (recon_mat - 1)
    elif wfs and etl:
        if not red_fact:
            red_fact = 1
        eff_echo_sp = (((1000 * wfs)/(434.215 * (etl + 1)))/red_fact)
        tot_read_time = 0.001 * eff_echo_sp * etl
    elif pix_band and etl:
        eff_echo_sp = ((1/(pix_band * etl)) * (etl - 1))
        tot_read_time = eff_echo_sp * (etl - 1)
    elif pix_band and recon_mat:
        eff_echo_sp = ((1/(pix_band * recon_mat)) * (recon_mat - 1))
        tot_read_time = eff_echo_sp * (recon_mat - 1)
    else:
        eff_echo_sp = "unknown"
        tot_read_time = "unknown"
        
    return eff_echo_sp,tot_read_time