# -*- coding: utf-8 -*-
"""Tests for the `convert_image_data` function.

NOTE: 
    * The test DICOM data used here is publicly available:
        * Referenced citation(s): convert_source/convert_source/tests/test.study_dir/TEST001-UNIT001/data.dicom/citation.[bib][json]
        * Website: https://zenodo.org/record/16956#.YBw5kI9Kgq0
        * Download link: https://zenodo.org/api/files/03deb9b8-e9a8-4727-a560-beff99b843db/DICOM.zip
    * Some parameter data is missing, likely due to the anonymization process.
"""
import pytest

import os
import sys
import pathlib
import platform
import urllib.request
import shutil

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import (
    Command,
    ConversionError,
    DependencyError
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info,
    convert_image_data
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
data_dir: str = os.path.join(os.getcwd(),'test.study_dir')
dcm_test_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','ST000000')

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

def test_data_conversion():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".PAR", ".nii"])
    assert len(subs_data) == 3

    data: str = subs_data[1].data
    [img, json, bval, bvec] = convert_image_data(data,'test_img',os.getcwd())

    assert os.path.exists(img[0]) == True
    
    for i in range(len(img)):
        if os.path.exists(img[i]):
            os.remove(img[i])
        if os.path.exists(json[i]):
            os.remove(json[i])

    data: str = subs_data[0].data
    
    with pytest.raises(ConversionError):
        [img, json, bval, bvec] = convert_image_data(data,'test_img',os.getcwd())
    
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
    
    os.remove("dcm2niix")
    assert os.path.exists("dcm2niix") == False
