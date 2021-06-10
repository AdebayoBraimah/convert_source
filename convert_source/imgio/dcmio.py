# -*- coding: utf-8 -*-
"""DICOM specific functions for convert_source. Primarily intended for converting and renaming DICOM files to BIDS NIFTI.
"""
import pydicom
import re
import os

from typing import (
    List,
    Optional, 
    Union
)

# Define class(es)
class DICOMerror(Exception):
    pass

# Define function(s)
def get_scan_time(dcm_file: str) -> Union[float,str]:
    """Reads the scan time from the DICOM header.

    Arguments:
        dcm_file: DICOM file.

    Returns:
        Acquisition duration (scan time, in s) as a float if it exists, or an empty string otherwise.
    """

    # Load data
    ds = pydicom.dcmread(dcm_file,force=True)

    # Gets scan time
    try:
        return ds.AcquisitionDuration
    except AttributeError:
        return ""

def is_valid_dcm(dcm_file: str,
                 raise_exc: Optional[bool] = False, 
                 verbose: Optional[bool] = False
                 ) -> bool:
    """Checks for a valid DICOM file by inspecting the conversion type label in the DICOM file header.
    This field should be blank. If this label is populated, then it is likely a secondary capture image 
    and thus is not likely to contain meaningful image information.
    
    Arguments:
        dcm_file: DICOM file.
        raise_exc: Raises exception in the case that execution needs to be halted.
        verbose: Enable verbosity.
    
    Returns: 
        True if DICOM file is not a secondary capture (or does not have text in the conversion type label field), and False otherwise.
    
    Raises:
        DICOMerror: Error that arises if the DICOM in question is not a valid DICOM, and the 'raise_exc' option is set to True.
    """

    dcm_file: str = os.path.abspath(dcm_file)
    
    # Read DICOM file header
    ds = pydicom.dcmread(dcm_file,force=True)
    
    # Invalid files include secondary image captures, and are not suitable for 
    # NIFTI conversion as they are often not converted and cause problems.
    # This string should be empty. If it is populated, then it is likely a secondary capture.
    try:
        conv_type = ds.ConversionType
    except AttributeError:
        conv_type = ""
    
    if conv_type in '':
        return True
    else:
        if verbose:
            print(f"Please check Conversion Type (0008, 0064) in dicom header. The presented DICOM file is not a valid file: {dcm_file}.")
        if raise_exc:
            raise DICOMerror(f"Invalid DICOM series/file. Please check {dcm_file}")
        return False

def get_bwpppe(dcm_file: str) -> Union[float,str]:
    """Reads the Bandwidth Per Pixel PhaseEncode value from a DICOM header. 
    
    NOTE: 
        This DICOM field is usually left blank on Philips DICOM headers.
    
    Arguments:
        dcm_file: DICOM file.
        
    Returns:
        Bandwidth Per Pixel PhaseEncode value as a float, or empty string otherwise.
    """

    dcm_file: str = os.path.abspath(dcm_file)
    
    # Load data
    ds = pydicom.dcmread(dcm_file,force=True)
    
    # Get relevant DICOM field
    try:
        val_str = str(ds[0x0019, 0x1028])
        val_list: List[str] = val_str.split(" ")
        bwpppe: str = val_list[-1]
        return float(bwpppe)
    except (AttributeError,KeyError):
        return ""

def get_red_fact(dcm_file: str) -> float:
    """Extracts parallel reduction factor in-plane value (GRAPPA/SENSE) from file description in the DICOM 
    header for Philips MR scanners. This reduction factor is assumed to be 1 if a value cannot be found 
    from witin the DICOM header.
    
    Arguments:
        dcm_file: DICOM file.
        
    Returns:
        Parallel reduction factor in-plane value (e.g. SENSE/GRAPPA factor), or 1.0 if not specified.
    """

    dcm_file: str = os.path.abspath(dcm_file)

    # Load dicom data
    ds = pydicom.dcmread(dcm_file,force=True)
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

def get_mb(dcm_file: str) -> int:
    """Extracts multi-band acceleration factor from file description in the DICOM header for (philips MR scanners).
    If this information cannont be inferred from the DICOM header file description - then it is assumed to be 1.
    
    NOTE: 
        This is done via a regEx search as no DICOM tag stores this information explicitly.
    
    Arguments:
        dcm_file: DICOM file.
        
    Returns:
        Multi-band acceleration factor.
    """

    dcm_file: str = os.path.abspath(dcm_file)

    # Initialize mb to 1
    mb = 1

    # Load dicom data
    ds = pydicom.dcmread(dcm_file,force=True)

    # Get image descriptor
    line = ds.SeriesDescription
    match = re.search(r'MB.*?([0-9.-]+)', line, re.M | re.I)
    if match:
        mb = match.group(1)
        mb = int(mb)
    return mb
