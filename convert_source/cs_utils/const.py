# -*- coding: utf-8 -*-
"""Constants needed for several utility modules in convert_source.
The constant variables contained here include:

    * ``BIDS_INFO``: BIDS metadata dictionary of BIDS related fields.
    * ``BIDS_ORD_ARR``: Ordered array of BIDS metadata fields.
    * ``BIDS_PARAM``: BIDS related parameters used for naming NIFTI, and their corresponding JSON files.
"""
import os
import pathlib

from collections import OrderedDict
from typing import (
    Dict,
    List
)

from convert_source import __version__ as CS_VERSION

# Default configuration file
DEFAULT_CONFIG: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[1]),"config","config.default.yml")

# Default BIDS version
_bids_version_file: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[1]),"config","bids_version.txt")

with open(_bids_version_file, "r") as f: 
    _bids_version = f.read().replace('\n','')
    f.close()

DEFAULT_BIDS_VERSION: str = _bids_version

# IMPROVEMENT:
#   Store BIDS_INFO dict in a series of yml/
#       JSON files that correspond to some BIDS
#       version. 
# 
#   Additionally, make seperate directories
#       for each BIDS version that contains:
#           * bids_version.txt
#           * bids_info.yml
#           * bids_order.txt
#           * bids_param.yml
#           * README: link to BIDS documentation
# 
#   Implementation would likely include importing a
#       function that includes taking a BIDS version
#       as argument, and returning a tuple of constants.
#           * Issue: BIDS version needs to be passed as 
#               argument prior to other function uses.
#           * Pass BIDS version as an argument to all 
#               parent and child classes/functions.
# 
# Empty BIDS metadata dictionary
BIDS_INFO: Dict = {
    # Common metadata
    ## Scanner Hardware
    "Manufacturer":None,
    "ManufacturersModelName":None,
    "DeviceSerialNumber":None,
    "StationName":None,
    "SoftwareVersions":None,
    "HardcopyDeviceSoftwareVersion":None,
    "MagneticFieldStrength":None,
    "ReceiveCoilName":None,
    "ReceiveCoilActiveElements":None,
    "GradientSetType":None,
    "MRTransmitCoilSequence":None,
    "MatrixCoilMode":None,
    "CoilCombinationMethod":None,
    ## Sequence Specifics
    "PulseSequenceType":None,
    "ScanningSequence":None,
    "SequenceVariant":None,
    "ScanOptions":None,
    "SequenceName":None,
    "PulseSequenceDetails":None,
    "NonlinearGradientCorrection":None,
    ## In-Plane Spatial Encoding
    "NumberShots":None,
    "ParallelReductionFactorInPlane":None,
    "ParallelAcquisitionTechnique":None,
    "PartialFourier":None,
    "PartialFourierDirection":None,
    "PhaseEncodingDirection":None,
    "EffectiveEchoSpacing":None,
    "TotalReadoutTime":None,
    ## Timing Parameters
    "EchoTime":None,
    "InversionTime":None,
    "SliceTiming":None,
    "SliceEncodingDirection":None,
    "DwellTime":None,
    ## RF & Contrast
    "FlipAngle":None,
    "NegativeContrast":None,
    ## Slice Acceleration
    "MultibandAccelerationFactor":None,
    ## Anatomical landmarks
    "AnatomicalLandmarkCoordinates":None,
    ## Institution information
    "InstitutionName":None,
    "InstitutionAddress":None,
    "InstitutionalDepartmentName":None,
    # Anat
    "ContrastBolusIngredient":None,
    # Func
    "RepetitionTime":None,
    "TaskName":None,
    "NumberOfVolumesDiscardedByScanner":None,
    "NumberOfVolumesDiscardedByUser":None,
    "DelayTime":None,
    "AcquisitionDuration":None,
    "DelayAfterTrigger":None,
    "Instructions":None,
    "TaskDescription":None,
    "CogAtlasID":None,
    "CogPOID":None,
    # Fmap
    "Units":None,
    "IntendedFor":None,
    # Custom BIDS fields
    "SourceDataFormat":None,
    "BIDSVersion":DEFAULT_BIDS_VERSION,
    "ConvertSourceVersion": CS_VERSION
}

# Ordered array of BIDS metadata fields
BIDS_ORD_ARR: List[str] = [
    "Manufacturer",
    "ManufacturersModelName",
    "DeviceSerialNumber",
    "StationName",
    "SoftwareVersions",
    "HardcopyDeviceSoftwareVersion",
    "MagneticFieldStrength",
    "ReceiveCoilName",
    "ReceiveCoilActiveElements",
    "GradientSetType",
    "MRTransmitCoilSequence",
    "MatrixCoilMode",
    "CoilCombinationMethod",
    "PulseSequenceType",
    "ScanningSequence",
    "SequenceVariant",
    "ScanOptions",
    "SequenceName",
    "PulseSequenceDetails",
    "NonlinearGradientCorrection",
    "NumberShots",
    "ParallelReductionFactorInPlane",
    "ParallelAcquisitionTechnique",
    "PartialFourier",
    "PartialFourierDirection",
    "PhaseEncodingDirection",
    "EffectiveEchoSpacing",
    "TotalReadoutTime",
    "EchoTime",
    "InversionTime",
    "SliceTiming",
    "SliceEncodingDirection",
    "DwellTime",
    "FlipAngle",
    "NegativeContrast",
    "MultibandAccelerationFactor",
    "AnatomicalLandmarkCoordinates",
    "InstitutionName",
    "InstitutionAddress",
    "InstitutionalDepartmentName",
    "ContrastBolusIngredient",
    "RepetitionTime",
    "TaskName",
    "NumberOfVolumesDiscardedByScanner",
    "NumberOfVolumesDiscardedByUser",
    "DelayTime",
    "AcquisitionDuration",
    "DelayAfterTrigger",
    "Instructions",
    "TaskDescription",
    "CogAtlasID",
    "CogPOID",
    "Units",
    "IntendedFor",
    "SourceDataFormat",
    "BIDSVersion",
    "ConvertSourceVersion"
]

# Empty BIDS parameter dictionary for naming files
BIDS_PARAM: Dict[str,str] = {
    "info":{
        "sub":"",
        "ses":""
    },
    "anat":{
        "acq":"",
        "ce":"",
        "rec":"",
        "run":"",
        "modality_label":""
    },
    "func":{
        "task":"",
        "acq":"",
        "ce":"",
        "dir":"",
        "rec":"",
        "run":"",
        "echo":"",
        "modality_label":""
    },
    "dwi":{
        "acq":"",
        "dir":"",
        "run":"",
        "modality_label":""
    },
    "fmap":{
        "acq":"",
        "run":"",
        # Case 1: Phase difference image and at least one magnitude image
        "case1":{
            "phasediff":"",
            "magnitude1":"",
            "magnitude2":""
        },
        # Case 2: Two phase images and two magnitude images
        "case2":{
            "phase1":"",
            "phase2":"",
            "magnitude1":"",
            "magnitude2":""
        },
        # Case 3: A real fieldmap image
        "case3":{
            "magnitude":"",
            "fieldmap":""
        },
        # Case 4: Multiple phase encoded directions ("pepolar")
        "case4":{
            "ce":"",
            "dir":"",
            "modality_label": "epi"
        }
    }
}

# SQL Database tables/columns names 
#   mapped to corresponding data types
DB_TABLES: OrderedDict = OrderedDict({
    'file_id':      'TEXT',    # PRIMARY KEY
    'rel_path':     'TEXT',
    'file_date':    'TEXT',
    'acq_date':     'TEXT',
    'sub_id':       'TEXT',
    'ses_id':       'TEXT',
    'bids_name':    'TEXT'
})

