# -*- coding: utf-8 -*-
"""Tests for convert_source's batch processing functions.
"""
import pytest

import os
import sys
import pathlib
import platform
import urllib.request
import shutil

from copy import deepcopy
from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError
)

from convert_source.cs_utils.const import BIDS_PARAM
from convert_source.cs_utils.bids_info import construct_bids_name

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info,
    comp_dict,
    depth,
    get_metadata
)

from convert_source.batch_convert import (
    read_config,
    bids_id,
    make_bids_name,
    data_to_bids,
    batch_proc
)

# Maximally compress data:
# GZIP=-9 tar -cvzf <file.tar.gz> <directory>

# Uncompress tar.gz files:
# tar -zxvf <file.tar.gz>

# Windows commands
# 
# Unzip on windows command line (windows 10): tar -xf <file.zip>
# 
# Recursively remove directories (and files, PowerShell): Remove-Item <directory> -Recurse
# Recursively remove directories (and files, cmd): del /s /q /f <directory>
# Recursively remove directories (and files, cmd): rmdir /s /q /f <directory>

# Test variables
scripts_dir: str = os.path.join(os.getcwd(),'helper.scripts')
test_config1: str = os.path.join(scripts_dir,'test.1.config.yml')
test_config2: str = os.path.join(scripts_dir,'test.2.config.yml')

data_dir: str = os.path.join(os.getcwd(),'test.study_dir')
dcm_test_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','ST000000')

out_dir: str = os.path.join(os.getcwd(),'test.bids')

## Additional test variables
meta_dict_1: Dict = {
    'Manufacturer': 'Vendor',
    'ManufacturersModelName': 'Scanner model',
    'MagneticFieldStrength': 3,
    'InstitutionName': 'Institution Name'
}

meta_dict_2: Dict = {}

def test_download_prog():
    class PlatformInferError(Exception):
        pass

    if platform.system().lower() == 'darwin':
        url: str = "https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20201102/dcm2niix_mac.zip"
        file_name: str = "dcm2niix_mac.zip"
    elif platform.system().lower() == 'windows':
        url: str = "https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20201102/dcm2niix_win.zip"
        file_name: str = "dcm2niix_win.zip"
    elif platform.system().lower() == 'linux':
        url: str = "https://github.com/rordenlab/dcm2niix/releases/download/v1.0.20201102/dcm2niix_lnx.zip"
        file_name: str = "dcm2niix_lin.zip"
    else:
        raise PlatformInferError("Unable to infer this platform's operating system.")

    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    
    assert os.path.exists(file_name) == True
    
    extract: Command = Command("tar")
    extract.cmd_list.append("-zxvf")
    extract.cmd_list.append(file_name)
    extract.run()

    os.remove(file_name)
    assert os.path.exists(file_name) == False

def test_dependency():
    dcm2niix_cmd: Command = Command("dcm2niix")

    with pytest.raises(DependencyError):
        assert dcm2niix_cmd.check_dependency(path_envs=[]) == False
    
    assert dcm2niix_cmd.check_dependency(path_envs=[os.getcwd()]) == True

def test_extract_data():
    dcm_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','data.tar.gz')
    extract: Command = Command("tar")
    extract.cmd_list.append("-zxvf")
    extract.cmd_list.append(dcm_data)
    extract.cmd_list.append("-C")
    extract.cmd_list.append(
        os.path.dirname(dcm_data)
    )
    extract.run()
    assert os.path.exists(dcm_test_data) == True

def test_read_config():
    verbose: bool = True
    [search_dict,
     bids_search,
     bids_map,
     meta_dict,
     exclusion_list] = read_config(config_file=test_config1,
                                   verbose=verbose)
    # write test statements here.
    assert depth(search_dict) == 4
    assert list(search_dict.keys()) == ['anat', 'func', 'fmap', 'swi', 'dwi']

    assert depth(bids_search) == 5
    assert list(bids_search.keys()) == ['anat', 'func', 'fmap', 'swi', 'dwi']

    assert depth(bids_map) == 5
    assert list(bids_map.keys()) == ['anat', 'func', 'fmap', 'swi', 'dwi']

    assert depth(meta_dict) == 4
    assert list(meta_dict.keys()) == ['common', 'func', 'dwi', 'fmap']

    assert comp_dict(bids_search,bids_map) == True

    with pytest.raises(KeyError):
        assert comp_dict(search_dict,meta_dict) == False

def get_subject_data():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[])
    assert len(subs_data) == 14

def test_bids_id():
    verbose: bool = True
    [search_dict,
    bids_search,
    bids_map,
    meta_dict,
    exclusion_list] = read_config(config_file=test_config1,
                                  verbose=verbose)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir, 
                                                exclusion_list=[])

    # DICOM file 1 (incomplete acquisition)
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[0].sub
    if subs_data[0].ses:
        bids_name_dict['info']['ses'] = subs_data[0].ses
    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[0].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)
    assert modality_type == 'anat'
    assert modality_label == 'T1w'
    assert task == ""

    # DICOM file 2 (complete acquisition)
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[1].sub
    if subs_data[1].ses:
        bids_name_dict['info']['ses'] = subs_data[1].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[1].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)
    assert modality_type == 'anat'
    assert modality_label == 'T2w'
    assert task == ""

    # NIFTI file
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[9].sub
    if subs_data[9].ses:
        bids_name_dict['info']['ses'] = subs_data[9].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[9].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)
    assert modality_type == 'func'
    assert modality_label == 'bold'
    assert task == 'rest'

    # PAR file
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[11].sub
    if subs_data[11].ses:
        bids_name_dict['info']['ses'] = subs_data[11].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[11].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)
    assert modality_type == 'swi'
    assert modality_label == 'swi'
    assert task == ""

def test_get_metadata():
    verbose: bool = True
    [search_dict,
    bids_search,
    bids_map,
    meta_dict,
    exclusion_list] = read_config(config_file=test_config1,
                                  verbose=verbose)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir, 
                                                exclusion_list=[])

    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[11].sub
    if subs_data[11].ses:
        bids_name_dict['info']['ses'] = subs_data[11].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[11].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)

    [meta_com_dict, 
    meta_scan_dict] = get_metadata(dictionary=meta_dict,
                                   modality_type=modality_type,
                                   task=task)

    assert meta_com_dict == meta_dict_1
    assert meta_scan_dict == meta_dict_2
    
def test_data_to_bids():
    verbose: bool = True
    [search_dict,
    bids_search,
    bids_map,
    meta_dict,
    exclusion_list] = read_config(config_file=test_config1,
                                  verbose=verbose)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir, 
                                                exclusion_list=[])

    # Test 1
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[0].sub
    if subs_data[0].ses:
        bids_name_dict['info']['ses'] = subs_data[0].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[0].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)

    [meta_com_dict, 
    meta_scan_dict] = get_metadata(dictionary=meta_dict,
                                   modality_type=modality_type,
                                   task=task)

    [imgs,
    jsons,
    bvals,
    bvecs] = data_to_bids(sub_data=subs_data[0],
                        bids_name_dict=bids_name_dict,
                        out_dir=out_dir,
                        modality_type=modality_type,
                        modality_label=modality_label,
                        task=task,
                        meta_dict=meta_com_dict,
                        mod_dict=meta_scan_dict)

    bids_imgs: List = []
    bids_jsons: List = []
    bids_bvals: List = []
    bids_bvecs: List = []

    bids_imgs.extend(imgs)
    bids_jsons.extend(jsons)
    bids_bvals.extend(bvals)
    bids_bvecs.extend(bvecs)

    assert len(bids_imgs) == 1
    assert len(bids_jsons) == 1
    assert len(bids_bvals) == 1
    assert len(bids_bvecs) == 1

    # Test 2
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[1].sub
    if subs_data[1].ses:
        bids_name_dict['info']['ses'] = subs_data[1].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[1].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)

    [meta_com_dict, 
    meta_scan_dict] = get_metadata(dictionary=meta_dict,
                                   modality_type=modality_type,
                                   task=task)

    [imgs,
    jsons,
    bvals,
    bvecs] = data_to_bids(sub_data=subs_data[1],
                        bids_name_dict=bids_name_dict,
                        out_dir=out_dir,
                        modality_type=modality_type,
                        modality_label=modality_label,
                        task=task,
                        meta_dict=meta_com_dict,
                        mod_dict=meta_scan_dict)

    bids_imgs: List = []
    bids_jsons: List = []
    bids_bvals: List = []
    bids_bvecs: List = []

    bids_imgs.extend(imgs)
    bids_jsons.extend(jsons)
    bids_bvals.extend(bvals)
    bids_bvecs.extend(bvecs)

    assert len(bids_imgs) == 2
    assert len(bids_jsons) == 2
    assert len(bids_bvals) == 2
    assert len(bids_bvecs) == 2

    ## These strings should be empty - only DWIs have these
    assert bids_bvals[0] == ""
    assert bids_bvecs[0] == ""

    # Test 3
    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[9].sub
    if subs_data[9].ses:
        bids_name_dict['info']['ses'] = subs_data[9].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[9].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)

    [meta_com_dict, 
    meta_scan_dict] = get_metadata(dictionary=meta_dict,
                                   modality_type=modality_type,
                                   task=task)

    [imgs,
    jsons,
    bvals,
    bvecs] = data_to_bids(sub_data=subs_data[9],
                        bids_name_dict=bids_name_dict,
                        out_dir=out_dir,
                        modality_type=modality_type,
                        modality_label=modality_label,
                        task=task,
                        meta_dict=meta_com_dict,
                        mod_dict=meta_scan_dict)

    bids_imgs: List = []
    bids_jsons: List = []
    bids_bvals: List = []
    bids_bvecs: List = []

    bids_imgs.extend(imgs)
    bids_jsons.extend(jsons)
    bids_bvals.extend(bvals)
    bids_bvecs.extend(bvecs)

    assert len(bids_imgs) == 1
    assert len(bids_jsons) == 1
    assert len(bids_bvals) == 1
    assert len(bids_bvecs) == 1

    ## These strings should be empty - only DWIs have these
    assert bids_bvals[0] == ""
    assert bids_bvecs[0] == ""

def test_tmp_cleanup():
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False

def test_make_bids_name():
    verbose: bool = True
    [search_dict,
    bids_search,
    bids_map,
    meta_dict,
    exclusion_list] = read_config(config_file=test_config1,
                                  verbose=verbose)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir, 
                                                exclusion_list=[])

    bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    bids_name_dict['info']['sub'] = subs_data[9].sub
    if subs_data[9].ses:
        bids_name_dict['info']['ses'] = subs_data[9].ses

    [bids_name_dict, 
    modality_type, 
    modality_label, 
    task] = bids_id(s=subs_data[9].data,
                    search_dict=search_dict,
                    bids_search=bids_search,
                    bids_map=bids_map,
                    bids_name_dict=bids_name_dict,
                    parent_dir=data_dir)

    bids_name_dict = construct_bids_name(sub_data=subs_data[9],
                                         modality_type=modality_type,
                                         modality_label=modality_label,
                                         task=task,
                                         out_dir=out_dir,
                                         zero_pad=2)

    [bids_1, bids_2, bids_3, bids_4] = make_bids_name(bids_name_dict=bids_name_dict,
                                                      modality_type=modality_type)

    assert bids_1 == "sub-TEST001_ses-UNIT001_task-rest_run-01_bold"
    assert bids_2 == "sub-TEST001_ses-UNIT001_task-rest_run-02_bold"
    assert bids_3 == "sub-TEST001_ses-UNIT001_task-rest_run-03_bold"
    assert bids_4 == "sub-TEST001_ses-UNIT001_task-rest_run-04_bold"

def test_batch_proc():
    # NOTE: test_config2 excludes PAR file test data, as
    #   the test data included only contains the PAR
    #   headers, and not the associated REC imaging 
    #   data.

    [imgs,
     jsons,
     bvals,
     bvecs] = batch_proc(config_file=test_config2,
                         study_img_dir=data_dir,
                         out_dir=out_dir,
                         verbose=True)

    assert len(imgs) == 11
    assert len(jsons) == 11
    assert len(bvals) == 11
    assert len(bvecs) == 11

def test_cleanup():
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False

    shutil.rmtree(dcm_test_data)
    assert os.path.exists(dcm_test_data) == False

    os.remove("dcm2niix")
