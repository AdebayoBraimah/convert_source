# -*- coding: utf-8 -*-
"""Tests for the cs_utils' utils module's functions.

NOTE: 
    * get_metadata is tested elsewhere.
    * convert_image_data is tested elsewhere.
    * header_search is tested elsewhere.
        * This function wraps `get_dcm_scan_tech` and `get_par_scan_tech`.

TODO: 
    * Raise warning for components/functions that are not tested.
"""
import pytest

import os
import pathlib
import sys
import platform

from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError,
    File
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    zeropad,
    get_echo,
    gzip_file,
    gunzip_file,
    read_json,
    write_json,
    update_json,
    dict_multi_update,
    get_bvals,
    list_in_substr,
    collect_info,
    comp_dict,
    depth,
    list_dict
)

# Test variables
scripts_dir: str = os.path.join(os.getcwd(),'helper.scripts')
tmp_out: str = os.path.join(os.getcwd(),'tmp.subs.dir')
tmp_json: str = os.path.join(scripts_dir,'test.orig.json')

## Test dictionary
tmp_dict: Dict = {
    "Manufacturer": "",
    "ManufacturersModelName": "",
    "DeviceSerialNumber": "",
    "StationName": "",
    "SoftwareVersions": "",
    "HardcopyDeviceSoftwareVersion": "",
    "MagneticFieldStrength": "",
    "ReceiveCoilName": "",
    "ReceiveCoilActiveElements": "",
    "GradientSetType": "",
    "MRTransmitCoilSequence": "",
    "MatrixCoilMode": "",
    "CoilCombinationMethod": "",
    "PulseSequenceType": "",
    "ScanningSequence": "",
    "SequenceVariant": "",
    "ScanOptions": "",
    "SequenceName": "",
    "PulseSequenceDetails": "",
    "NonlinearGradientCorrection": "",
    "NumberShots": "",
    "ParallelReductionFactorInPlane": "",
    "ParallelAcquisitionTechnique": "",
    "PartialFourier": "",
    "PartialFourierDirection": "",
    "PhaseEncodingDirection": "",
    "EffectiveEchoSpacing": "",
    "TotalReadoutTime": "",
    "EchoTime": 0.093,
    "InversionTime": "",
    "SliceTiming": "",
    "SliceEncodingDirection": "",
    "DwellTime": "",
    "FlipAngle": 65,
    "NegativeContrast": "",
    "MultibandAccelerationFactor": "4",
    "AnatomicalLandmarkCoordinates": "",
    "InstitutionName": "",
    "InstitutionAddress": "",
    "InstitutionalDepartmentName": "",
    "ContrastBolusIngredient": "",
    "RepetitionTime": "",
    "VolumeTiming": "",
    "TaskName": "Resting State",
    "NumberOfVolumesDiscardedByScanner": 5,
    "NumberOfVolumesDiscardedByUser": "0",
    "DelayTime": "",
    "AcquisitionDuration": "",
    "DelayAfterTrigger": "",
    "Instructions": "",
    "TaskDescription": "",
    "CogAtlasID": "",
    "CogPOID": "",
    "Units": "",
    "IntendedFor": "",
    "SourceDataFormat": "",
    "BIDSVersion": "1.4.1"
}

def test_create_util_test_dir():
    if platform.system().lower() != 'windows':
        assert os.path.exists(scripts_dir) == True

        script_label: str = os.path.join(scripts_dir,'test.file_structure.sh')
        mk_test_dir: Command = Command(script_label)
        assert mk_test_dir.check_dependency() == True

        mk_test_dir.cmd_list.append("--out-dir")
        mk_test_dir.cmd_list.append(tmp_out)
        mk_test_dir.run()
        assert os.path.exists(tmp_out) == True

def test_zeropad():
    x: int = 5
    y: int = 10
    z: float = 0.2

    assert zeropad(x,3) == '005'
    assert zeropad(x,1) == '5'
    assert zeropad(y,5) == '00010'
    with pytest.raises(TypeError):
        assert zeropad(z,3) == '00.2'

def test_get_echo():
    assert get_echo(json_file=tmp_json) == 0.093

def test_gzip_file():
    with File("test.txt") as f:
        f.touch()
        ff: str = gzip_file(f.file)
        assert os.path.abspath(ff) == os.path.abspath("test.txt.gz")

def test_gunzip_file():
    ff: str = gunzip_file("test.txt.gz")
    assert os.path.abspath(ff) == os.path.abspath("test.txt")
    os.remove(ff)

def test_read_json():
    tt = read_json(tmp_json)
    assert tt == tmp_dict

def test_write_json():
    x: str = "test.json"
    write_json(x,tmp_dict)
    assert os.path.exists(x) == True

def test_update_json():
    tt: Dict = {"MagneticFieldStrength": 3}
    x: str = update_json("test.json",tt)
    f: Dict = read_json("test.json")
    assert f['MagneticFieldStrength'] == 3
    os.remove("test.json")

def test_dict_multi_update():
    td1: Dict = {"Field1":"string1"}
    td2: Dict = {"Field2":"string2"}
    td3: Dict = {"Field3":"string3"}

    td4: Dict = {"Field1":"string1",
                 "Field2":"string2",
                 "Field3":"string3"}

    td5: Dict = dict_multi_update(dictionary=None,
                                  **td1,
                                  **td2,
                                  **td3)
    assert td4 == td5

def test_get_bvals():
    x: str = "test.bval"
    with File(x) as f:
        f.write_txt("0 0 800 2000 3000")
        bvals: List[str] = get_bvals(f.file)
    assert bvals == [ 800, 2000, 3000 ]
    os.remove("test.bval")

def test_list_in_substr():
    list1: List[str] = ['T1','rest','FMAP']
    list2: List[str] = ['T2','stroop','DWI']

    str1: str = "ThisStringHasReStBUTnotAlways"
    str2: str = "AlternatingTextWithAndNbAckT2"

    assert list_in_substr(list1,str1) == True
    assert list_in_substr(list2,str1) == False

    assert list_in_substr(list1,str2) == False
    assert list_in_substr(list2,str2) == True

def test_collect_info():
    if platform.system().lower() != 'windows':
        parent_dir: str = tmp_out
        exclusion_list: List[str] = ['T1','DWI','SWI']
        data: List[SubDataInfo] = collect_info(parent_dir,exclusion_list)
        print (len(data))
        assert len(data) == 252

def test_comp_dict_funcs():
    d1: Dict[str,str] = {"level1":{"sub1":"subLevel1"},
                         "level2":"sub2"}
    d2: Dict[str,str] = {"level1":{"sub1":"subLevel1"},
                         "level2":"sub2"}
    d3: Dict[str,str] = {"levela":{"subb":"subLevelc"},
                         "leveld":{"sube":"subLevelf"}}
    d4: Dict[str,str] = {"levela":{"subb":"subLevelc"},
                         "leveld":{"sube":None}}

    assert comp_dict(d1,d2) == True
    with pytest.raises(KeyError):
        assert comp_dict(d1,d3) == False
    with pytest.raises(ValueError):
        assert comp_dict(d3,d4)
    assert depth(d1) == 3
    assert depth(d2) == 3
    assert depth(d3) == 3
    assert depth(d4) == 3

    assert len(list_dict(d1)) == 2
    assert len(list_dict(d2)) == 2
    assert len(list_dict(d3)) == 2
    assert len(list_dict(d4)) == 2

def test_cleanup_tmp_dir():
    if platform.system().lower() != 'windows':
        rm_test_dir: Command = Command("rm")
        rm_test_dir.cmd_list.append("-rf")
        rm_test_dir.cmd_list.append(tmp_out)
        rm_test_dir.run()
        assert os.path.exists(tmp_out) == False

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)
