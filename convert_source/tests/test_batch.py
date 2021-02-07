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

from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import Command

from convert_source.cs_utils.utils import (
    list_dict,
    comp_dict,
    depth
)

from convert_source.batch_convert import (
    BIDSImgData,
    read_config,
    bids_id,
    _gather_bids_name_args,
    _get_bids_name_args,
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



