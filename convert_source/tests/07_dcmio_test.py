# -*- coding: utf-8 -*-
"""Tests for the imgio's dcmio module's functions.
"""

# NOTE: 
#     * The test DICOM data used here is publicly available:
#         * Referenced citation(s): convert_source/convert_source/tests/test.study_dir/TEST001-UNIT001/data.dicom/citation.[bib][json]
#         * Website: https://zenodo.org/record/16956#.YBw5kI9Kgq0
#         * Download link: https://zenodo.org/api/files/03deb9b8-e9a8-4727-a560-beff99b843db/DICOM.zip
#     * Some parameter data is missing, likely due to the anonymization process.

import pytest

import os
import sys
import pathlib
import platform

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info
)

from convert_source.imgio.dcmio import (
    is_valid_dcm,
    get_scan_time,
    get_red_fact,
    get_bwpppe,
    get_mb
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
data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'test.study_dir'))
dcm_test_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','ST000000')

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

def get_subject_data():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])
    assert len(subs_data) == 3

# NOTE: subs_data list of SubDataInfo objects is placed in each test function
#   as pytest does not allow test functions to execute without first initializing
#   all global variables.

def test_is_valid_dcm():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert is_valid_dcm(data) == True
    assert sub == 'TEST001'
    assert ses == 'UNIT001'

def test_get_scan_time():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_scan_time(data) == ''

def test_get_bwpppe():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_bwpppe(data) == ''

def test_get_red_fact():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_red_fact(data) == 1.0

def test_get_mb():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_mb(data) == 1 

def test_cleanup():
    del_method: bool = False
    rm_method: bool = False
    rm_item_method: bool = False

    if platform.system().lower() != 'windows':
        rm_test_dir: Command = Command("rm")
        rm_test_dir.cmd_list.append("-rf")
        rm_test_dir.cmd_list.append(dcm_test_data)
        rm_test_dir.run()
        assert os.path.exists(dcm_test_data) == False
    else:
        try:
            rm_test_dir: Command = Command("del")
            rm_test_dir.check_dependency()
            del_method: bool = True
        except DependencyError:
            rm_test_dir: Command = Command("rmdir")
            rm_test_dir.check_dependency()
            rm_method: bool = True
        except DependencyError:
            rm_test_dir: Command = Command("Remove-Item")
            rm_test_dir.check_dependency()
            rm_item_method: bool = True
        except DependencyError:
            import shutil
            shutil.rmtree(dcm_test_data)
            assert os.path.exists(dcm_test_data) == False
        
        if rm_method or del_method:
            rm_test_dir.cmd_list.append("/s")
            rm_test_dir.cmd_list.append("/q")
            rm_test_dir.cmd_list.append("/f")
            rm_test_dir.cmd_list.append(dcm_test_data)
            rm_test_dir.run()
            assert os.path.exists(dcm_test_data) == False
        elif rm_item_method:
            rm_test_dir.cmd_list.append(dcm_test_data)
            rm_test_dir.cmd_list.append("-Recurse")
            rm_test_dir.run()
            assert os.path.exists(dcm_test_data) == False

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)