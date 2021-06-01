# -*- coding: utf-8 -*-
"""Tests for the imgio's pario module's functions.
"""
import os
import sys
import pathlib
import shutil

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.database import create_db

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info
)

from convert_source.imgio.pario import (
    get_echo_time,
    get_etl,
    get_mb,
    get_red_fact,
    get_scan_time,
    get_wfs,
    get_flip_angle
)

# Test variables
data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'test.study_dir'))

out_dir: str = os.path.join(os.getcwd(),'test.file.study')
misc_dir: str = os.path.join(out_dir,'.misc')
test_db: str = os.path.join(misc_dir,'study.db')

# # Create output test directory
# if os.path.exists(misc_dir):
#     pass
# else:
#     os.makedirs(misc_dir)

# create_db(database=test_db)

def get_subject_data():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".dcm", ".nii"])
    
    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    file_id: str = subs_data[0].file_id
    
    assert len(subs_data) == 4
    assert sub == 'TEST001'
    assert ses == 'UNIT001'
    assert file_id == '0000001'

# def test_cleanup_1():
#     """NOTE: This test currently FAILS on Windows operating systems."""
#     shutil.rmtree(misc_dir)
#     assert os.path.exists(misc_dir) == False

def test_get_etl():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_etl(data1) == 1
    assert get_etl(data2) == 71

def test_cleanup_2():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_wfs():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_wfs(data1) == 2.268
    assert get_wfs(data2) == 31.376

def test_cleanup_3():
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
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_red_fact(data1) == 1.0
    assert get_red_fact(data2) == 1.0

def test_cleanup_4():
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
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_mb(data1) == 1
    assert get_mb(data2) == 4

def test_cleanup_5():
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
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_scan_time(data1) == 186.0
    assert get_scan_time(data2) == 15.0

def test_cleanup_6():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_echo_time():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    # NOTE: This is in msec, and may be updated soon.
    assert get_echo_time(data1) == 0.0034
    assert get_echo_time(data2) == 0.0930

def test_cleanup_7():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(misc_dir)
    assert os.path.exists(misc_dir) == False

def test_get_flip_angle():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    create_db(database=test_db)

    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                database=test_db,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_flip_angle(data1) == 11.0
    assert get_flip_angle(data2) == 90.0

def test_cleanup_8():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)
