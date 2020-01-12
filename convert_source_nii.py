# -*- coding: utf-8 -*-
'''
Contains all the necessary functions to rename
nifti images in BIDS format.
'''
#
# 
# -*- coding: utf-8 -*-
# title           : convertSourceNifti.py
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2020 01 08 18:32:16
# version         : 0.0.1
# usage           : convertSourceNifti.py [-h,--help]
# notes           : [notes]
# python_version  : 3.7.4
#==============================================================================

# Import Modules

import os
import shutil
import glob
import subprocess
import random
import re
import json
import pandas as pd
import nibabel as nib
from scipy import stats

# Random integer max range value
n = 10000

def update_json(json_file, bvalue='unknown', wfs='unknown', epi_factor='unknown', acc=1, mb=1, scan_time='unknown', acq_tech ='unknown', task_name=""):
    '''
    Appends additional information not normally included in the JSON file side car
    as dcm2niix does not normally look for these in PAR/XML REC headers.
    '''

    # "epi_factor":epi_factor changed to "EchoTrainLength":epi_factor
    # for easier JSON parsing.

    if task_name == "":
        # In the case of empty task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "ParallelAcquisitionTechnique": acq_tech,
            "ParallelReductionFactorInPlane": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time,
            "SourceDataFormat": "PAR_REC"}
    else:
        # In the case of populated task_name string
        data = {"WaterFatShift": wfs, "EchoTrainLength": epi_factor,
            "ParallelAcquisitionTechnique": acq_tech,
            "ParallelReductionFactorInPlane": acc, "MultibandAccelerationFactor": mb,
            "bvalue": bvalue, "scan_time": scan_time, "TaskName": task_name,
            "SourceDataFormat": "PAR_REC"}

    with open(json_file, "r") as read_file:
        data2 = json.load(read_file)

    data2.update(data)

    with open(json_file, 'w+') as outfile:
        json.dump(data2, outfile, indent=4)

    return json_file

def get_num_runs(out_dir, task="", acq="", dirs="", bval="", scan=""):
    '''
    Determines run number of a scan (e.g. T1w, T2w, bold, dwi etc.)
    in an output directory by globbing the directory for the number
    of compressed niftis of the same scan.
    '''

    runs = os.path.join(out_dir, f"*{task}*{acq}*{dirs}*{bval}*{scan}*.nii*")
    run_num = len(glob.glob(runs))
    run_num = run_num + 1

    return run_num

def get_echo(json_file):
    '''
    Gets the echo time (TE) from a 
    JSON sidecar file for an acquisition.
    '''
    with open(json_file, "r") as read_file:
        data = json.load(read_file)

    echo = data.get("EchoTime")

    return echo

def get_num_frames(nii_file):
    '''Gets the number of frames for a DW or fMR image series.'''

    img = nib.load(nii_file)
    frames = img.header.get_data_shape()
    num_frames = frames[3]

    # num_frames = subprocess.check_output(["fslval", nii_file, "dim4"])
    # num_frames = str(num_frames)
    # num_frames = int(re.sub('[^0-9]', '', num_frames))  # Strip non-numeric information
    return num_frames
