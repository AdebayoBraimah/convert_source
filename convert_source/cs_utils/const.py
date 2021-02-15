# -*- coding: utf-8 -*-
"""Constants needed for several utility modules in convert_source.
The constant variables contained here include:

    * ``BIDS_INFO``: BIDS metadata dictionary of BIDS related fields.
    * ``BIDS_ORD_ARR``: Ordered array of BIDS metadata fields.
    * ``BIDS_PARAM``: BIDS related parameters used for naming NIFTI, and their corresponding JSON files.
"""
import os
import pathlib
from typing import (
    Dict,
    List
)

from convert_source import __version__

# Default configuration file
DEFAULT_CONFIG: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]),"config","config.default.yml")

# Default BIDS version
_bids_version_file: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]),"config","bids_version.txt")

with open(_bids_version_file, "r") as f: 
    _bids_version = f.read().replace('\n','')

DEFAULT_BIDS_VERSION: str = _bids_version

CS_VERSION: str = __version__

# Empty BIDS metadata dictionary
BIDS_INFO: Dict = {
    # Common metadata
    ## Scanner Hardware
    "Manufacturer":"",
    "ManufacturersModelName":"",
    "DeviceSerialNumber":"",
    "StationName":"",
    "SoftwareVersions":"",
    "HardcopyDeviceSoftwareVersion":"",
    "MagneticFieldStrength":"",
    "ReceiveCoilName":"",
    "ReceiveCoilActiveElements":"",
    "GradientSetType":"",
    "MRTransmitCoilSequence":"",
    "MatrixCoilMode":"",
    "CoilCombinationMethod":"",
    ## Sequence Specifics
    "PulseSequenceType":"",
    "ScanningSequence":"",
    "SequenceVariant":"",
    "ScanOptions":"",
    "SequenceName":"",
    "PulseSequenceDetails":"",
    "NonlinearGradientCorrection":"",
    ## In-Plane Spatial Encoding
    "NumberShots":"",
    "ParallelReductionFactorInPlane":"",
    "ParallelAcquisitionTechnique":"",
    "PartialFourier":"",
    "PartialFourierDirection":"",
    "PhaseEncodingDirection":"",
    "EffectiveEchoSpacing":"",
    "TotalReadoutTime":"",
    ## Timing Parameters
    "EchoTime":"",
    "InversionTime":"",
    "SliceTiming":"",
    "SliceEncodingDirection":"",
    "DwellTime":"",
    ## RF & Contrast
    "FlipAngle":"",
    "NegativeContrast":"",
    ## Slice Acceleration
    "MultibandAccelerationFactor":"",
    ## Anatomical landmarks
    "AnatomicalLandmarkCoordinates":"",
    ## Institution information
    "InstitutionName":"",
    "InstitutionAddress":"",
    "InstitutionalDepartmentName":"",
    # Anat
    "ContrastBolusIngredient":"",
    # Func
    "RepetitionTime":"",
    "VolumeTiming":"",
    "TaskName":"",
    "NumberOfVolumesDiscardedByScanner":"",
    "NumberOfVolumesDiscardedByUser":"",
    "DelayTime":"",
    "AcquisitionDuration":"",
    "DelayAfterTrigger":"",
    "Instructions":"",
    "TaskDescription":"",
    "CogAtlasID":"",
    "CogPOID":"",
    # Fmap
    "Units":"",
    "IntendedFor":"",
    # Custom BIDS fields
    "SourceDataFormat":"",
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
    "VolumeTiming",
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
