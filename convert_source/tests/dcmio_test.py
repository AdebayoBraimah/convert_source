# -*- coding: utf-8 -*-
"""Tests for the imgio's dcmio module's main functions.

NOTE: 
    * get_metadata is tested elsewhere.
    * convert_image_data is tested elsewhere.
    * header_search is tested elsewhere.
        * This function wraps `get_dcm_scan_tech` and `get_par_scan_tech`.
"""

from convert_source.cs_utils.utils import SubDataInfo
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

# # CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info
)

# from convert_source.imgio.dcmio import (
#     # imports
# )

# Maximally compress data:
# GZIP=-9 tar -cvzf <file.tar.gz> <directory>

# Windows commands
# 
# Unzip on windows command line (windows 10): tar -xf <file.zip>
# 
# Recursively remove directories (and files, PowerShell): Remove-Item <directory> -Recurse
# Recursively remove directories (and files, cmd): del /s /q /f <directory>
# Recursively remove directories (and files, cmd): rmdir /s /q /f <directory>
# 
# Uncompress *.tar.gz file: tar -zxvf <file.tar.gz>

# Test variables
data_dir: str = os.path.join(os.getcwd(),'test.study_dir','TEST001-UNIT001')
dcm_test_data: str = os.path.join(data_dir,'data.dicom','ST000000')
tmp_out: str = os.path.join(os.getcwd(),'tmp.subs.dir')
scripts_dir: str = os.path.join(os.getcwd(),'helper.scripts')
tmp_json: str = os.path.join(scripts_dir,'test.orig.json')

def test_extract_data():
    dcm_data: str = os.path.join(data_dir,'data.dicom','data.tar.gz')
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

# Intermediary test variables
subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                            exclusion_list=[".PAR", ".nii"])

sub: str = subs_data[0].sub
ses: str = subs_data[0].ses
data: str = subs_data[0].data

def test_get_scan_time():

# def test_cleanup():
#     del_method: bool = False
#     rm_method: bool = False
#     rm_item_method: bool = False

#     if platform.system().lower() != 'windows':
#         rm_test_dir: Command = Command("rm")
#         rm_test_dir.cmd_list.append("-rf")
#         rm_test_dir.cmd_list.append(dcm_test_data)
#         rm_test_dir.run()
#         assert os.path.exists(dcm_test_data) == False
#     else:
#         try:
#             rm_test_dir: Command = Command("del")
#             rm_test_dir.check_dependency()
#             del_method: bool = True
#         except DependencyError:
#             rm_test_dir: Command = Command("rmdir")
#             rm_test_dir.check_dependency()
#             rm_method: bool = True
#         except DependencyError:
#             rm_test_dir: Command = Command("Remove-Item")
#             rm_test_dir.check_dependency()
#             rm_item_method: bool = True
#         except DependencyError:
#             import shutil
#             shutil.rmtree(dcm_test_data)
#             assert os.path.exists(dcm_test_data) == False
        
#         if rm_method or del_method:
#             rm_test_dir.cmd_list.append("/s")
#             rm_test_dir.cmd_list.append("/q")
#             rm_test_dir.cmd_list.append("/f")
#             rm_test_dir.cmd_list.append(dcm_test_data)
#             rm_test_dir.run()
#             assert os.path.exists(dcm_test_data) == False
#         elif rm_item_method:
#             rm_test_dir.cmd_list.append(dcm_test_data)
#             rm_test_dir.cmd_list.append("-Recurse")
#             rm_test_dir.run()
#             assert os.path.exists(dcm_test_data) == False

