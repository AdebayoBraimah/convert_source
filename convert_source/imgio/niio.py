# -*- coding: utf-8 -*-
"""NIFTI specific functions for convert_source. Primarily intended for renaming NIFTI to be BIDS compliant.
"""
import os
# import shutil
# import random
import nibabel as nib
# import nibabel.filebasedimages.ImageFileError
from nibabel.filebasedimages import ImageFileError

from decimal import Decimal

from typing import (
    Dict, 
    Optional, 
    Union
)

from convert_source.imgio.dcmio import(
    get_red_fact as dcm_red_fact,
    get_mb as dcm_mb,
    get_scan_time as dcm_scan_time
)

from convert_source.imgio.pario import(
    get_wfs,
    get_mb as par_mb,
    get_red_fact as par_red_fact,
    get_scan_time as par_scan_time,
    get_etl,
    get_echo_time as par_echo,
    get_flip_angle as par_flip_angle
)

from convert_source.cs_utils.utils import calc_read_time

# Define function(s)
def get_nii_tr(nii_file: str) -> Union[float,str]:
    """Reads the NIFTI file header and returns the repetition time (TR, sec) as a value if it is not zero, otherwise this 
    function returns an string.
    
    Arguments:
        nii_file: NIFTI image filename.
        
    Returns: 
        Repetition time (TR, sec), if not zero, or an empty string otherwise.
    """
    nii_file: str = os.path.abspath(nii_file)
    
    try:
        # Load nifti file and store TR
        img = nib.load(nii_file)
        tr = float(round(Decimal(float(img.header['pixdim'][4])),3))

        # Check if TR is likely
        if tr == 0:
            return ""
        else:
            return tr
    except ImageFileError:
        return ""

def get_num_frames(nii_file: str) -> int:
    """Determines the number of frames/volumes/TRs in a NIFTI-2 file.

    Arguments:
        nii_file: NIFTI image file.

    Returns:
        Number of temporal frames or volumes in NIFTI file.
    """
    nii_file: str = os.path.abspath(nii_file)
    
    try:
        img = nib.load(nii_file)
        dims = img.header.get_data_shape()
        return dims[3]
    except (IndexError,ImageFileError):
        return  1

def get_data_params(file: str,
                    json_file: Optional[str] = "", 
                    ) -> Dict:
    """Creates a dictionary of key mapped parameter items that are often not written to the BIDS JSON sidecar
    when converting Philips DICOM and PAR REC files.
    
    Arguments:
        file: Filepath to raw image data file (DICOM or PAR REC).
        json_file: Corresponding JSON sidecare file.
    
    Returns:
        Dictionary of BIDS related key mapped items/values.
    """
    if json_file:
        json_file: str = os.path.abspath(json_file)
    else:
        json_file: str = ""
    
    # Create empty dictionary
    tmp_dict: Dict = {}
    
    # Check file type
    if '.dcm' in file.lower():
        red_fact: float = dcm_red_fact(file)
        mb: int = dcm_mb(file)
        scan_time: Union[float,str] = dcm_scan_time(file)
        [eff_echo_sp, tot_read_time]  = calc_read_time(file,json_file)
        source_format: str = "DICOM"
        tmp_dict.update({"ParallelReductionFactorInPlane": red_fact,
                         "MultibandAccelerationFactor": mb,
                         "EffectiveEchoSpacing": eff_echo_sp,
                         "TotalReadoutTime": tot_read_time,
                         "AcquisitionDuration": scan_time,
                         "SourceDataFormat": source_format})
    elif 'par' in file.lower():
        wfs: float = get_wfs(file)
        red_fact: float = par_red_fact(file)
        mb: int = par_mb(file)
        scan_time: Union[float,str] = par_scan_time(file)
        etl: int = get_etl(file)
        [eff_echo_sp, tot_read_time]  = calc_read_time(file,json_file)
        echo_time = par_echo(file)
        flip_angle = par_flip_angle(file)
        source_format: str = "PAR REC"
        tmp_dict.update({"WaterFatShift": wfs,
                         "ParallelAcquisitionTechnique": 'SENSE',
                         "ParallelReductionFactorInPlane": red_fact,
                         "MultibandAccelerationFactor": mb,
                         "EffectiveEchoSpacing": eff_echo_sp,
                         "TotalReadoutTime": tot_read_time,
                         "AcquisitionDuration": scan_time,
                         "EchoTrainLength": etl,
                         "EchoTime": echo_time,
                         "FlipAngle": flip_angle,
                         "SourceDataFormat": source_format})
    elif 'nii' in file.lower():
        tr: Union[float,str] = get_nii_tr(file)
        source_format: str = "NIFTI"
        tmp_dict.update({"RepetitionTime": tr,
                         "SourceDataFormat": source_format})
    else:
        pass
        
    info: Dict = {}
    info.update(tmp_dict)
    
    return info
