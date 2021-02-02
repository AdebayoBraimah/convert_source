# -*- coding: utf-8 -*-
"""Tests for the cs_utils utils module main functions.

TODO:
    * functions to test:
        * get_echo
        * gzip_file
        * gunzip_file
        * read_json
        * write_josn
        * update_json
        * dict_multi_update
        * get_bvals
        * get_metadata
        * list_in_substr
        * convert_image_data
        * glob_dcm
        * glob_img
        * img_exclude
        * collect_info
        * get_recon_mat
        * get_pix_band
        * calc_read_time
        * comp_dict
        * depth
        * list_dict
        * get_par_scan_tech
        * get_dcm_scan_tech
        * header_search
"""

import pytest

import os
import pathlib
import sys

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

# # CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError
)

from convert_source.cs_utils.utils import (
    zeropad,
)

# Test variables
scripts_dir = os.path.join(os.getcwd(),'helper.scripts')
tmp_out = os.path.join(os.getcwd(),'tmp.subs.dir')

# def test_create_util_test_dir():
#     scripts_dir = os.path.join(os.getcwd(),'helper.scripts')
#     assert os.path.exists(scripts_dir) == True
# 
#     script_label = os.path.join(scripts_dir,'test.file_structure.sh')
#     mk_test_dir = Command(script_label)
#     assert mk_test_dir.check_dependency() == True
# 
#     tmp_out = os.path.join(os.getcwd(),'tmp.subs.dir')
#     mk_test_dir.cmd_list.append("--out-dir")
#     mk_test_dir.cmd_list.append(tmp_out)
#     mk_test_dir.run()
#     assert os.path.exists(tmp_out) == True

def test_zeropad():
    x: int = 5
    y: int = 10
    z: float = 0.2

    assert zeropad(x,3) == '005'
    assert zeropad(x,1) == '5'
    assert zeropad(y,5) == '00010'
    with pytest.raises(TypeError):
        assert zeropad(z,3) == '00.2'




