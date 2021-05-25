# -*- coding: utf-8 -*-
"""Tests for convert_source's batch symbolic linking functions.
"""
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

from convert_source.cs_utils.fileio import Command

from convert_source.batch_symlink import (
    batch_link,
    read_file_to_list,
    create_study_sym_links
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

def test_read_file_to_list():
    assert read_file_to_list(file=test_infile) == ['TEST001-UNIT001']
    assert read_file_to_list(file=test_mapfile) == ['001-001']

def test_create_study_sym_links():
    sym_links: List[str] = create_study_sym_links(study_dir=data_dir,
                                                infile=test_infile,
                                                mapfile=test_mapfile,
                                                outdir=out_dir)
    assert os.path.exists(out_dir) == True
    assert os.path.exists(os.path.join(out_dir,sym_links[0])) == True
    assert os.path.islink(os.path.join(out_dir,sym_links[0])) == True

    shutil.rmtree(out_dir)
    assert os.path.exists(os.path.join(out_dir,sym_links[0])) == False

def test_batch_link():
    sym_links: List[str] = batch_link(study_dir=data_dir,
                                        infile=test_infile,
                                        mapfile=test_mapfile,
                                        out_dir=out_dir)
    assert os.path.exists(out_dir) == True
    assert os.path.exists(os.path.join(out_dir,sym_links[0])) == True
    assert os.path.islink(os.path.join(out_dir,sym_links[0])) == True

def test_cleanup():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False

    shutil.rmtree(dcm_test_data)
    assert os.path.exists(dcm_test_data) == False

    os.remove("dcm2niix")
