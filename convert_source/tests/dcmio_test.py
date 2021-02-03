# -*- coding: utf-8 -*-
"""Tests for the imgio's dcmio module's main functions.

NOTE: 
    * get_metadata is tested elsewhere.
    * convert_image_data is tested elsewhere.
    * header_search is tested elsewhere.
        * This function wraps `get_dcm_scan_tech` and `get_par_scan_tech`.
"""

import pytest

import os
import pathlib
import sys

from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

# # CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)

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
scripts_dir: str = os.path.join(os.getcwd(),'TEST001-UNIT001','data.dicom')
tmp_out: str = os.path.join(os.getcwd(),'tmp.subs.dir')
tmp_json: str = os.path.join(scripts_dir,'test.orig.json')