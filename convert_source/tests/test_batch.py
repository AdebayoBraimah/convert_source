# -*- coding: utf-8 -*-
"""Tests for convert_source's batch processing functions.
"""
import pytest

import os
import sys
import pathlib
import platform

from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import ConversionError

from convert_source.batch_convert import (
    BIDSImgData,
    read_config,
    bids_id,
    _gather_bids_name_args,
    _get_bids_name_args,
    _make_bids_name,
    data_to_bids,
    batch_proc
)

# Test variables
scripts_dir: str = os.path.join(os.getcwd(),'helper.scripts')
test_config: str = os.path.join(scripts_dir,'test.config.yml')

data_dir: str = os.path.join(os.getcwd(),'test.study_dir')
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

def test_read_config():
    verbose: bool = True
    [search_dict,
     bids_search,
     bids_map,
     meta_dict,
     exclusion_list] = read_config(config_file=test_config,
                                   verbose=verbose)
    # write test statements here.

