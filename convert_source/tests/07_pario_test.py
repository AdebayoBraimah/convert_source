# -*- coding: utf-8 -*-
"""Tests for the imgio's pario module's functions.
"""
import pytest

import os
import sys
import pathlib

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

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

data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'test.study_dir'))

def get_subject_data():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses
    data: str = subs_data[0].data
    
    assert len(subs_data) == 4
    assert sub == 'TEST001'
    assert ses == 'UNIT001'

def test_get_etl():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_etl(data1) == 1
    assert get_etl(data2) == 71

def test_get_wfs():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_wfs(data1) == 2.268
    assert get_wfs(data2) == 31.376

def test_get_red_fact():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_red_fact(data1) == 1.0
    assert get_red_fact(data2) == 1.0

def test_get_mb():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_mb(data1) == 1
    assert get_mb(data2) == 4

def test_get_scan_time():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_scan_time(data1) == 186.0
    assert get_scan_time(data2) == 15.0

def test_get_echo_time():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    # NOTE: This is in msec, and may be updated soon.
    assert get_echo_time(data1) == 0.0034
    assert get_echo_time(data2) == 0.0930

def test_get_flip_angle():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm", ".nii"])
    
    data1: str = subs_data[0].data
    data2: str = subs_data[3].data

    assert get_flip_angle(data1) == 11.0
    assert get_flip_angle(data2) == 90.0

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)