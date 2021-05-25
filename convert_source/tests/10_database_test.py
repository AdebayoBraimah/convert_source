# -*- coding: utf-8 -*-
"""Tests for convert_source's database module and its associated functions.
"""
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

from convert_source.cs_utils.database import (
    construct_db_dict,
    create_db,
    insert_row_db,
    get_len_rows,
    get_file_id,
    update_table_row,
    export_dataframe,
    export_scans_dataframe,
    _get_dir_relative_path,
    _export_tmp_bids_df,
    export_bids_scans_dataframe,
    query_db,
    _zeropad
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
scripts_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'helper.scripts'))
test_config1: str = os.path.join(scripts_dir,'test.1.config.yml')
test_config2: str = os.path.join(scripts_dir,'test.2.config.yml')

data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'test.study_dir'))
dcm_test_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','ST000000')

test_infile: str = os.path.join(scripts_dir,'test.orig_subject_id.txt')
test_mapfile: str = os.path.join(scripts_dir,'test.map_subject_id.txt')

out_dir: str = os.path.join(os.getcwd(),'test.study.link')
misc_dir: str = os.path.join(out_dir,'.misc')
test_db: str = os.path.join(misc_dir,'test.study.db')

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
    
    if platform.system().lower() == 'windows':
        extract: Command = Command("tar")
        extract.cmd_list.append("-zxvf")
        extract.cmd_list.append(file_name)
        extract.run()
    else:
        extract: Command = Command("unzip")
        extract.cmd_list.append(file_name)
        extract.run()

    os.remove(file_name)
    assert os.path.exists(file_name) == False

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

def test_create_db():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)
    
    assert os.path.exists(create_db(database=test_db)) == True
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False
