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
import convert_source_dcm as cdm
import convert_source_par as csp
import utils

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

def get_num_frames(nii_file):
    '''
    Determines the number of frames/volumes/TRs in a NifTi-2 file.

    Arguments:
        nii_file (string): Absolute filepath to NifTi image file

    Returns:
        num_frames (int): Number of temporal frames or volumes in NifTi file.
    '''
    
    try:
        img = nib.load(nii_file)
        dims = img.header.get_data_shape()
        num_frames = dims[3]
    except IndexError:
        num_frames = 1
        pass
    
    return num_frames

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
        bval_list = utils.get_bvals(bval_file)
        tmp_dict.update({"bval":bval_list})
    
    # Check file type
    if '.dcm' in file.lower():
        red_fact = cdm.get_red_fact(file)
        mb = cdm.get_mb(file)
        scan_time = cdm.get_scan_time(file)
        [eff_echo_sp, tot_read_time]  = utils.calc_read_time(file,json_file)
        source_format = "DICOM"
        tmp_dict.update({"ParallelReductionFactorInPlane": red_fact,
                         "MultibandAccelerationFactor": mb,
                         "EffectiveEchoSpacing": eff_echo_sp,
                         "TotalReadoutTime": tot_read_time,
                         "AcquisitionDuration": scan_time,
                         "SourceDataFormat": source_format})
    elif 'PAR' in file.upper():
        wfs = csp.get_wfs(file)
        red_fact = csp.get_red_fact(file)
        mb = csp.get_mb(file)
        scan_time = csp.get_scan_time(file)
        etl = csp.get_etl(file)
        [eff_echo_sp, tot_read_time]  = utils.calc_read_time(file,json_file)
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

def data_to_bids_anat(bids_out_dir, file, sub, scan, meta_dict_com=dict(), meta_dict_anat=dict(), ses=1, scan_type='anat'):
    '''
    Renames converted NifTi-2 files to conform with the BIDS naming convension (in the case of anatomical files).
    This function accepts any image file (DICOM, PAR REC, and NifTi-2). If the image file is a raw data file (e.g. DICOM, PAR REC)
    it is converted to NifTi first, then renamed. The output BIDS directory need not exist at runtime.
    
    Arguments:
        bids_out_dir (string): Path to output BIDS directory. 
        file (string): Filepath to image file.
        sub (int or string): Subject ID
        scan (string): Modality (e.g. T1w, T2w, or SWI)
        meta_dict_com (dict): Metadata dictionary for common image metadata
        meta_dict_anat (dict): Metadata dictionary for common anatomical image specific metadata
        ses (int or string): Session ID
        scan_type (string): BIDS sub-directory scan type. Valid options include, but are not limited to: anat (default), func, fmap, dwi, etc.
        
    Returns:
        out_nii (string): Absolute filepath to gzipped output NifTi-2 file
        out_json (string): Absolute filepath to corresponding JSON file
    '''

    # Use try-except statement here in the case of invalid/incomplete image files that will throw errors in dcm2niix
    try:
        # Create Output Directory Variables
        # Zeropad subject ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass
        # Zeropad session ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass

        out_dir = os.path.join(bids_out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

        # Make output directory
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Get absolute filepaths
        bids_out_dir = os.path.abspath(bids_out_dir)
        out_dir = os.path.abspath(out_dir)

        # Create temporary output names/directories
        n = 10000 # maximum N for random number generator
        tmp_out_dir = os.path.join(bids_out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
        tmp_basename = 'tmp_basename' + str(random.randint(0, n))

        if not os.path.exists(tmp_out_dir):
            os.makedirs(tmp_out_dir)

        # Convert image file
        # Check file extension in file
        if '.nii.gz' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.nii' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            nii_file = utils.gzip_file(nii_file)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.dcm' in file or '.PAR' in file:
            [nii_file, json_file] = utils.convert_anat(file,tmp_out_dir,tmp_basename)
        else:
            [nii_file, json_file] = utils.convert_anat(file,tmp_out_dir,tmp_basename)

        # Get additional sequence/modality parameters
        if os.path.exists(json_file):
            meta_dict_params = get_data_params(file, json_file)
        else:
            tmp_json = ""
            meta_dict_params = get_data_params(file, tmp_json)

        # Update JSON file
        info = dict()
        info = utils.dict_multi_update(info,**meta_dict_params)
        info = utils.dict_multi_update(info,**meta_dict_com)
        info = utils.dict_multi_update(info,**meta_dict_anat)

        json_file = utils.update_json(json_file,info)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)

        info = dict()
        info = utils.read_json(json_file)

        # Append w to T1/T2 if not already done
        if scan in 'T1' or scan in 'T2':
            scan = scan + 'w'

        # Query dictionary for acquisition/naming keys
        try:
            acq = info['acq']
        except KeyError:
            acq = ""
            pass
        try:
            ce = info['ce']
        except KeyError:
            ce = ""
            pass
        try:
            rec = info['rec']
        except KeyError:
            rec = ""
            pass

        # Create output filename
        out_name = f"sub-{sub}" + f"_ses-{sub}"
        name_run_dict = dict()

        if acq:
            out_name = out_name + f"_acq-{acq}"
            tmp_dict = {"acq":f"{acq}"}
            name_run_dict.update(tmp_dict)

        if ce:
            out_name = out_name + f"_ce-{ce}"
            tmp_dict = {"ce":f"{ce}"}
            name_run_dict.update(tmp_dict)

        if rec:
            out_name = out_name + f"_rec-{rec}"
            tmp_dict = {"rec":f"{rec}"}
            name_run_dict.update(tmp_dict)

        # Get Run number
        run = utils.get_num_runs(out_dir, scan=scan, **name_run_dict)
        run = '{:02}'.format(run)

        if run:
            out_name = out_name + f"_run-{run}"

        out_name = out_name + f"_{scan}"


        out_nii = os.path.join(out_dir, out_name + '.nii.gz')
        out_json = os.path.join(out_dir, out_name + '.json')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)

        # remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)

        return out_nii,out_json
    except FileNotFoundError:
        print(f"Error: unable to convert {file}")
        pass

def data_to_bids_func(bids_out_dir, file, sub, scan, task = 'rest', meta_dict_com=dict(), meta_dict_func=dict(), ses=1, scan_type='func'):
    '''
    Renames converted NifTi-2 files to conform with the BIDS naming convension (in the case of functional files).
    This function accepts any image file (DICOM, PAR REC, and NifTi-2). If the image file is a raw data file (e.g. DICOM, PAR REC)
    it is converted to NifTi first, then renamed. The output BIDS directory need not exist at runtime.
    
    Arguments:
        bids_out_dir (string): Path to output BIDS directory. 
        file (string): Filepath to image file.
        sub (int or string): Subject ID
        scan (string): Modality (e.g. bold or cbv)
        task (string): Task for the fMR image data
        meta_dict_com (dict): Metadata dictionary for common image metadata
        meta_dict_func (dict): Metadata dictionary for common functional image specific metadata
        ses (int or string): Session ID
        scan_type (string): BIDS sub-directory scan type. Valid options include, but are not limited to: anat, func (default), fmap, dwi, etc.
        
    Returns:
        out_nii (string): Absolute filepath to gzipped output 4D NifTi-2 file
        out_json (string): Absolute filepath to corresponding JSON file
    '''

    # Use try-except statement here in the case of invalid/incomplete image files that will throw errors in dcm2niix
    try:
        # Create Output Directory Variables
        # Zeropad subject ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass
        # Zeropad session ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass

        out_dir = os.path.join(bids_out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

        # Make output directory
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Get absolute filepaths
        bids_out_dir = os.path.abspath(bids_out_dir)
        out_dir = os.path.abspath(out_dir)

        # Create temporary output names/directories
        n = 10000 # maximum N for random number generator
        tmp_out_dir = os.path.join(bids_out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
        tmp_basename = 'tmp_basename' + str(random.randint(0, n))

        if not os.path.exists(tmp_out_dir):
            os.makedirs(tmp_out_dir)

        # Convert image file
        # Check file extension in file
        if '.nii.gz' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.nii' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            nii_file = utils.gzip_file(nii_file)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.dcm' in file or '.PAR' in file:
            [nii_file, json_file] = utils.convert_anat(file,tmp_out_dir,tmp_basename)
        else:
            [nii_file, json_file] = utils.convert_anat(file,tmp_out_dir,tmp_basename)

        # Get additional sequence/modality parameters
        if os.path.exists(json_file):
            meta_dict_params = get_data_params(file, json_file)
        else:
            tmp_json = ""
            meta_dict_params = get_data_params(file, tmp_json)

        # Update JSON file
        info = dict()
        info = utils.dict_multi_update(info,**meta_dict_params)
        info = utils.dict_multi_update(info,**meta_dict_com)
        info = utils.dict_multi_update(info,**meta_dict_func)

        json_file = utils.update_json(json_file,info)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)

        info = dict()
        info = utils.read_json(json_file)

        # Decide if file is 4D timeseries or single-band reference
        num_frames = get_num_frames(nii_file)
        if num_frames == 1:
            scan = 'sbref'

        # Query dictionary for acquisition/naming keys
        try:
            acq = info['acq']
        except KeyError:
            acq = ""
            pass
        try:
            ce = info['ce']
        except KeyError:
            ce = ""
            pass
        try:
            direction = info['dir']
        except KeyError:
            direction = ""
            pass
        try:
            rec = info['rec']
        except KeyError:
            rec = ""
            pass
        try:
            echo = info['echo']
        except KeyError:
            echo = ""
            pass

        # Create output filename    
        out_name = f"sub-{sub}" + f"_ses-{ses}" + f"_task-{task}"

        name_run_dict = dict()
        tmp_dict = {"task":f"{task}"}
        name_run_dict.update(tmp_dict)

        if acq:
            out_name = out_name + f"_acq-{acq}"
            tmp_dict = {"acq":f"{acq}"}
            name_run_dict.update(tmp_dict)

        if ce:
            out_name = out_name + f"_ce-{ce}"
            tmp_dict = {"ce":f"{ce}"}
            name_run_dict.update(tmp_dict)

        if direction:
            out_name = out_name + f"_dir-{direction}"
            tmp_dict = {"dirs":f"{direction}"}
            name_run_dict.update(tmp_dict)

        if rec:
            out_name = out_name + f"_rec-{rec}"
            tmp_dict = {"rec":f"{rec}"}
            name_run_dict.update(tmp_dict)

        if echo:
            tmp_dict = {"echo":f"{echo}"}
            name_run_dict.update(tmp_dict)

        # Get Run number
        run = utils.get_num_runs(out_dir, scan=scan, **name_run_dict)
        run = '{:02}'.format(run)

        if run:
            out_name = out_name + f"_run-{run}"

        if echo:
            out_name = out_name + f"_echo-{echo}"

        out_name = out_name + f"_{scan}"


        out_nii = os.path.join(out_dir, out_name + '.nii.gz')
        out_json = os.path.join(out_dir, out_name + '.json')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)

        # remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)

        return out_nii,out_json
    except FileNotFoundError:
        print(f"Error: unable to convert {file}")
        pass

def data_to_bids_fmap(bids_out_dir, file, sub, scan='fieldmap', meta_dict_com=dict(), meta_dict_fmap=dict(), ses=1, scan_type='fmap'):
    '''
    Renames converted NifTi-2 files to conform with the BIDS naming convension (in the case of fieldmap files).
    This function accepts any image file (DICOM, PAR REC, and NifTi-2). If the image file is a raw data file (e.g. DICOM, PAR REC)
    it is converted to NifTi first, then renamed. The output BIDS directory need not exist at runtime.
    
    N.B.: This function is mainly designed to handle fieldmap data case 3 from bids-specifications document. Furhter support for 
    the additional cases requires test/validation data. 
    BIDS-specifications document located here: 
    https://github.com/bids-standard/bids-specification/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md
    
    Arguments:
        bids_out_dir (string): Path to output BIDS directory. 
        file (string): Filepath to image file.
        sub (int or string): Subject ID
        scan (string): Modality (e.g. fieldmap, magnitude, or phasediff)
        meta_dict_com (dict): Metadata dictionary for common image metadata
        meta_dict_fmap (dict): Metadata dictionary for common fieldmap image specific metadata
        ses (int or string): Session ID
        scan_type (string): BIDS sub-directory scan type. Valid options include, but are not limited to: anat, func, fmap (default), dwi, etc.
        
    Returns:
        out_nii_fmap (string): Absolute filepath to gzipped output NifTi-2 fieldmap image file
        out_nii_mag (string): Absolute filepath to gzipped output NifTi-2 magnitude image file
        out_json_fmap (string): Absolute filepath to correspond fieldmap image JSON sidecare
        out_json_mag (string): Absolute filepath to correspond magnitude image JSON sidecare
    '''

    # Use try-except statement here in the case of invalid/incomplete image files that will throw errors in dcm2niix
    try:
        # Create Output Directory Variables
        # Zeropad subject ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass
        # Zeropad session ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass

        out_dir = os.path.join(bids_out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

        # Make output directory
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Get absolute filepaths
        bids_out_dir = os.path.abspath(bids_out_dir)
        out_dir = os.path.abspath(out_dir)

        # Create temporary output names/directories
        n = 10000 # maximum N for random number generator
        tmp_out_dir = os.path.join(bids_out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
        tmp_basename = 'tmp_basename' + str(random.randint(0, n))

        if not os.path.exists(tmp_out_dir):
            os.makedirs(tmp_out_dir)

        # Convert image file
        # Check file extension in file
        if '.nii.gz' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.nii' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            nii_file = utils.gzip_file(nii_file)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                pass
        elif '.dcm' in file or '.PAR' in file:
            [nii_fmap, json_fmap, nii_mag, json_mag] = utils.convert_fmap(file,tmp_out_dir,tmp_basename)
        else:
            [nii_fmap, json_fmap, nii_mag, json_mag] = utils.convert_fmap(file,tmp_out_dir,tmp_basename)

        # Get additional sequence/modality parameters
        if os.path.exists(json_fmap):
            meta_dict_params = get_data_params(file, json_fmap)
        else:
            tmp_json = ""
            meta_dict_params = get_data_params(file, tmp_json)

        # Update JSON file
        info = dict()
        info = utils.dict_multi_update(info,**meta_dict_params)
        info = utils.dict_multi_update(info,**meta_dict_com)
        info = utils.dict_multi_update(info,**meta_dict_fmap)

        json_fmap = utils.update_json(json_fmap,info)
        json_mag = utils.update_json(json_mag,info)

        nii_fmap = os.path.abspath(nii_fmap)
        nii_mag = os.path.abspath(nii_mag)

        json_fmap = os.path.abspath(json_fmap)
        json_mag = os.path.abspath(json_mag)

        info = dict()
        info = utils.read_json(json_fmap)

        # Query dictionary for acquisition/naming keys
        try:
            acq = info['acq']
        except KeyError:
            acq = ""
            pass

        # Create output filename    
        out_name = f"sub-{sub}" + f"_ses-{ses}"
        name_run_dict = dict()

        if acq:
            out_name = out_name + f"_acq-{acq}"
            tmp_dict = {"acq":f"{acq}"}
            name_run_dict.update(tmp_dict)

        # Get Run number
        run = utils.get_num_runs(out_dir, scan=scan, **name_run_dict)
        run = '{:02}'.format(run)

        if run:
            out_name = out_name + f"_run-{run}"

        out_name = out_name + f"_{scan}"

        out_nii_fmap = os.path.join(out_dir, out_name + '_fieldmap' + '.nii.gz')
        out_nii_mag = os.path.join(out_dir, out_name + '_magnitude' + '.nii.gz')

        out_json_fmap = os.path.join(out_dir, out_name + '_fieldmap' + '.json')
        out_json_mag = os.path.join(out_dir, out_name + '_magnitude' + '.json')

        os.rename(nii_fmap, out_nii_fmap)
        os.rename(nii_mag, out_nii_mag)

        os.rename(json_fmap, out_json_fmap)
        os.rename(json_mag, out_json_mag)

        # Remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)

        return out_nii_fmap, out_nii_mag, out_json_fmap, out_json_mag
    except FileNotFoundError:
        print(f"Error: unable to convert {file}")
        pass

def data_to_bids_dwi(bids_out_dir, file, sub, scan='dwi', meta_dict_com=dict(), meta_dict_dwi=dict(), ses=1, scan_type='dwi'):
    '''
    Renames converted NifTi-2 files to conform with the BIDS naming convension (in the case of diffuion image files).
    This function accepts any image file (DICOM, PAR REC, and NifTi-2). If the image file is a raw data file (e.g. DICOM, PAR REC)
    it is converted to NifTi first, then renamed. The output BIDS directory need not exist at runtime. If the original
    data format is NifTi, bval and bvec files will be copied over should they exist, otherwise, they will not be
    generated.
    
    Arguments:
        bids_out_dir (string): Path to output BIDS directory. 
        file (string): Filepath to image file.
        sub (int or string): Subject ID
        scan (string): Modality (e.g. dwi, dki, etc)
        meta_dict_com (dict): Metadata dictionary for common image metadata
        meta_dict_dwi (dict): Metadata dictionary for common diffusion image specific metadata
        ses (int or string): Session ID
        scan_type (string): BIDS sub-directory scan type. Valid options include, but are not limited to: anat, func, fmap, dwi (default), etc.
        
    Returns:
        out_nii (string): Absolute filepath to gzipped output diffusion weighted NifTi-2 file
        out_json (string): Absolute filepath to corresponding JSON file
        out_bval (string): Absolute filepath to corresponding b-values file
        out_bvec (string): Absolute filepath to corresponding b-vectors file
    '''

    # Use try-except statement here in the case of invalid/incomplete image files that will throw errors in dcm2niix
    try:
        # Create Output Directory Variables
        # Zeropad subject ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass
        # Zeropad session ID if possible
        try:
            ses = '{:03}'.format(int(ses))
        except ValueError:
            pass

        out_dir = os.path.join(bids_out_dir, f"sub-{sub}", f"ses-{ses}", f"{scan_type}")

        # Make output directory
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Get absolute filepaths
        bids_out_dir = os.path.abspath(bids_out_dir)
        out_dir = os.path.abspath(out_dir)

        # Create temporary output names/directories
        n = 10000 # maximum N for random number generator
        tmp_out_dir = os.path.join(bids_out_dir, f"sub-{sub}", 'tmp_dir' + str(random.randint(0, n)))
        tmp_basename = 'tmp_basename' + str(random.randint(0, n))

        if not os.path.exists(tmp_out_dir):
            os.makedirs(tmp_out_dir)

        # Convert image file
        # Check file extension in file
        if '.nii.gz' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            bval = os.path.join(path,filename + '.bval*')
            bvec = os.path.join(path,filename + '.bvec*')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
                # Decide if file is DWI or single-band reference
                num_frames = get_num_frames(nii_file)
                if num_frames == 1:
                    scan = 'sbref'; bval = ""; bvec = ""
                else:
                    bval = utils.cp_file(bval, tmp_out_dir, tmp_basename)
                    bvec = utils.cp_file(bvec, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                bval = os.path.join(tmp_out_dir, tmp_basename + '.bval')
                bvec = os.path.join(tmp_out_dir, tmp_basename + '.bvec')
                # Decide if file is DWI or single-band reference
                num_frames = get_num_frames(nii_file)
                if num_frames == 1:
                    scan = 'sbref'; bval = ""; bvec = ""
                pass
        elif '.nii' in file:
            nii_file = utils.cp_file(file, tmp_out_dir, tmp_basename)
            nii_file = utils.gzip_file(nii_file)
            [path,filename,ext] = utils.file_parts(file)
            json_file = os.path.join(path,filename + '.json')
            bval = os.path.join(path,filename + '.bval*')
            bvec = os.path.join(path,filename + '.bvec*')
            try:
                json_file = utils.cp_file(json_file, tmp_out_dir, tmp_basename)
                # Decide if file is DWI or single-band reference
                num_frames = get_num_frames(nii_file)
                if num_frames == 1:
                    scan = 'sbref'; bval = ""; bvec = ""
                else:
                    bval = utils.cp_file(bval, tmp_out_dir, tmp_basename)
                    bvec = utils.cp_file(bvec, tmp_out_dir, tmp_basename)
            except FileNotFoundError:
                json_file = os.path.join(tmp_out_dir, tmp_basename + '.json')
                bval = os.path.join(tmp_out_dir, tmp_basename + '.bval')
                bvec = os.path.join(tmp_out_dir, tmp_basename + '.bvec')
                # Decide if file is DWI or single-band reference
                num_frames = get_num_frames(nii_file)
                if num_frames == 1:
                    scan = 'sbref'; bval = ""; bvec = ""
                pass
        elif '.dcm' in file or '.PAR' in file:
            [nii_file, json_file, bval, bvec] = utils.convert_dwi(file,tmp_out_dir,tmp_basename)
            # Decide if file is DWI or single-band reference
            num_frames = get_num_frames(nii_file)
            if num_frames == 1:
                scan = 'sbref'; bval = ""; bvec = ""
        else:
            [nii_file, json_file, bval, bvec] = utils.convert_dwi(file,tmp_out_dir,tmp_basename)
            # Decide if file is DWI or single-band reference
            num_frames = get_num_frames(nii_file)
            if num_frames == 1:
                scan = 'sbref'; bval = ""; bvec = ""

        # Get additional sequence/modality parameters
        if os.path.exists(json_file) and os.path.exists(bval):
            meta_dict_params = get_data_params(file, json_file, bval)
        elif os.path.exists(bval):
            tmp_json = ""
            meta_dict_params = get_data_params(file, tmp_json, bval)
        elif os.path.exists(json_file):
            tmp_bval = ""
            meta_dict_params = get_data_params(file, json_file, tmp_bval)
        else:
            tmp_json = ""
            tmp_bval = ""
            meta_dict_params = get_data_params(file, tmp_json, tmp_bval)

        # Update JSON file
        info = dict()
        info = utils.dict_multi_update(info,**meta_dict_params)
        info = utils.dict_multi_update(info,**meta_dict_com)
        info = utils.dict_multi_update(info,**meta_dict_dwi)

        json_file = utils.update_json(json_file,info)

        nii_file = os.path.abspath(nii_file)
        json_file = os.path.abspath(json_file)

        info = dict()
        info = utils.read_json(json_file)

        if bval and bvec:
            bval = os.path.abspath(bval)
            bvec = os.path.abspath(bvec)

        # Query dictionary for acquisition/naming keys
        try:
            acq = info['acq']
        except KeyError:
            acq = ""
            pass
        try:
            direction = info['dir']
        except KeyError:
            direction = ""
            pass

        # Non-standard acquisition/naming keys
        # Used in order to differentiate between DWI scans for multiple bvalues
        try:
            bvals = info['bval']
        except KeyError:
            bvals = list()
            pass
        try:
            echo_time = info['EchoTime']
            echo_time = int(echo_time * 1000)
        except KeyError:
            echo_time = ""
            pass

        # Create output filename    
        out_name = f"sub-{sub}" + f"_ses-{ses}"
        name_run_dict = dict()

        if bvals:
            vals = ""
            for val in bvals:
                vals = vals + 'b' + str(int(val))
        else:
            vals = 'b0'

        if vals and acq and echo_time:
            out_name = out_name + f"_acq-{acq}{vals}TE{echo_time}"
            tmp_dict = {"acq":f"{acq}{vals}TE{echo_time}"}
        elif vals and acq:
            out_name = out_name + f"_acq-{acq}{vals}"
            tmp_dict = {"acq":f"{acq}{vals}"}
        elif vals and echo_time:
            out_name = out_name + f"_acq-{vals}TE{echo_time}"
            tmp_dict = {"acq":f"{vals}TE{echo_time}"}
        elif acq and echo_time:
            out_name = out_name + f"_acq-{acq}TE{echo_time}"
            tmp_dict = {"acq":f"{acq}TE{echo_time}"}
        elif acq:
            out_name = out_name + f"_acq-{acq}"
            tmp_dict = {"acq":f"{acq}"}
        elif vals:
            out_name = out_name + f"_acq-{vals}"
            tmp_dict = {"acq":f"{vals}"}
        elif echo_time:
            out_name = out_name + f"_acq-TE{echo_time}"
            tmp_dict = {"acq":f"TE{echo_time}"}
        else:
            tmp_dict = dict()

        name_run_dict.update(tmp_dict)

        if direction:
            out_name = out_name + f"_dir-{direction}"
            tmp_dict = {"dirs":f"{direction}"}
            name_run_dict.update(tmp_dict)

        # Get Run number
        run = utils.get_num_runs(out_dir, scan=scan, **name_run_dict)
        run = '{:02}'.format(run)

        if run:
            out_name = out_name + f"_run-{run}"

        out_name = out_name + f"_{scan}"

        out_nii = os.path.join(out_dir, out_name + '.nii.gz')
        out_json = os.path.join(out_dir, out_name + '.json')

        out_bval = os.path.join(out_dir, out_name + '.bval')
        out_bvec = os.path.join(out_dir, out_name + '.bvec')

        os.rename(nii_file, out_nii)
        os.rename(json_file, out_json)

        if bval:
            os.rename(bval,out_bval)

        if bvec:
            os.rename(bvec,out_bvec)

        # remove temporary directory and leftover files
        shutil.rmtree(tmp_out_dir)

        if bval and bvec:
            return out_nii,out_json,out_bval,out_bvec
        elif not bval and bvec:
            return out_nii,out_json
    except FileNotFoundError:
        print(f"Error: unable to convert {file}")
        pass
