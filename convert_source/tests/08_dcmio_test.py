# -*- coding: utf-8 -*-
"""Tests for the imgio's dcmio module's functions.

NOTE: 
    * The test DICOM data used here is publicly available:
        * Referenced citation(s): convert_source/convert_source/tests/test.study_dir/TEST001-UNIT001/data.dicom/citation.[bib][json]
        * Website: https://zenodo.org/record/16956#.YBw5kI9Kgq0
        * Download link: https://zenodo.org/api/files/03deb9b8-e9a8-4727-a560-beff99b843db/DICOM.zip
    * Some parameter data is missing, likely due to the anonymization process.
"""
import os
import sys
import pathlib
import shutil

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command
)

from convert_source.cs_utils.database import create_db

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
# 
# Uncompress tar.gz files:
# tar -zxvf <file.tar.gz>
# 
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

out_dir: str = os.path.join(os.getcwd(),'test.study')
misc_dir: str = os.path.join(out_dir,'.misc')
test_db: str = os.path.join(misc_dir,'study.db')

# # Create output test directory
# if os.path.exists(misc_dir):
#     pass
# else:
#     os.makedirs(misc_dir)

# create_db(database=test_db)

def test_extract_data():
    dcm_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','data.1.tar.gz')
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
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])
    assert len(subs_data) == 3

# def test_cleanup_1():
#     """NOTE: This test currently FAILS on Windows operating systems."""
#     shutil.rmtree(misc_dir)
#     assert os.path.exists(misc_dir) == False

# NOTE: subs_data list of SubDataInfo objects is placed in each test function
#   as pytest does not allow test functions to execute without first initializing
#   all global variables.

def test_is_valid_dcm():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert is_valid_dcm(data) == True
    assert sub == 'TEST001'
    assert ses == 'UNIT001'

def test_cleanup_2():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_scan_time():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_scan_time(data) == ''

def test_cleanup_3():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_bwpppe():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_bwpppe(data) == ''

def test_cleanup_4():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_red_fact():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_red_fact(data) == 1.0

def test_cleanup_5():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_mb():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".PAR", ".nii"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    assert get_mb(data) == 1

def test_cleanup_6():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(out_dir)
    shutil.rmtree(dcm_test_data)
    assert os.path.exists(out_dir) == False
    assert os.path.exists(dcm_test_data) == False

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)