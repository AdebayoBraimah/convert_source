# -*- coding: utf-8 -*-
"""Tests for convert_source's database module and its associated functions.
"""
from sqlite3.dbapi2 import DatabaseError
import pytest
import os
import sys
import pathlib
import platform
import urllib.request
import shutil
import pandas as pd

from typing import Dict

import pytest

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.fileio import Command
from convert_source.batch_convert import read_config

from convert_source.cs_utils.database import (
    construct_db_dict,
    create_db,
    insert_row_db,
    get_file_id,
    get_len_rows,
    update_table_row,
    export_dataframe,
    export_scans_dataframe,
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

out_dir: str = os.path.join(os.getcwd(),'test.database.study')
misc_dir: str = os.path.join(out_dir,'.misc')
test_db: str = os.path.join(misc_dir,'test.study.db')

test_file_1: str = os.path.join(data_dir,'TEST001-UNIT001','data.dicom','ST000000','SE000001','MR000009.dcm')
test_file_2: str = os.path.join(data_dir,'TEST001-UNIT001','data.parrec','AXIAL.PAR')
test_file_3: str = os.path.join(data_dir,'TEST001-UNIT001','data.nifti','FLAIR.nii.gz')

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

def test_construct_db_dict_and_insert_row_db():
    if os.path.exists(misc_dir):
        pass
    else:
        os.makedirs(misc_dir)

    create_db(database=test_db)

    use_dcm_dir: bool = True

    with pytest.raises(DatabaseError):
        error_dict: Dict[str,str] = construct_db_dict(
                                                    study_dir=data_dir,
                                                    sub_id='001',
                                                    file_name=test_file_1,
                                                    use_dcm_dir=use_dcm_dir
                                                )

    test_dict_1: Dict[str,str] = construct_db_dict(
                                                    study_dir=data_dir,
                                                    sub_id='001',
                                                    ses_id='001',
                                                    database=test_db,
                                                    file_name=test_file_1,
                                                    use_dcm_dir=use_dcm_dir
                                                )
    insert_row_db(database=test_db, info=test_dict_1)
    test_dict_2: Dict[str,str] = construct_db_dict(
                                                    study_dir=data_dir,
                                                    sub_id='101',
                                                    ses_id='1',
                                                    database=test_db,
                                                    file_name=test_file_2
                                                )
    insert_row_db(database=test_db, info=test_dict_2)
    test_dict_3: Dict[str,str] = construct_db_dict(
                                                    study_dir=data_dir,
                                                    sub_id='CX009902',
                                                    ses_id='BMNC000XDF',
                                                    database=test_db,
                                                    file_name=test_file_3
                                                )
    insert_row_db(database=test_db, info=test_dict_3)

    # Test statements
    # 
    # NOTE:
    #   The test statement/assertion was commented out
    #       as the acq date-time is from when the file
    #       was created (e.g. in the case of NIFTI files).
    assert get_len_rows(database=test_db) == 3

    assert test_dict_1.get('file_id','') == '0000001'
    assert test_dict_1.get('sub_id','') == '001'
    assert test_dict_1.get('ses_id','') == '001'
    assert test_dict_1.get('acq_date','') == '2015-01-14T13:26:28'
    assert test_dict_1.get('bids_name','') == ''

    assert test_dict_2.get('file_id','') == '0000002'
    assert test_dict_2.get('sub_id','') == '101'
    assert test_dict_2.get('ses_id','') == '1'
    assert test_dict_2.get('acq_date','') == '2018-04-19T09:38:14'
    assert test_dict_2.get('bids_name','') == ''

    assert test_dict_3.get('file_id','') == '0000003'
    assert test_dict_3.get('sub_id','') == 'CX009902'
    assert test_dict_3.get('ses_id','') == 'BMNC000XDF'
    # assert test_dict_3.get('acq_date','') == '2021-05-31T10:52:50'
    assert test_dict_3.get('bids_name','') == ''

def test_get_row_len():
    assert get_len_rows(database=test_db) == 3

def test_get_file_id():
    assert get_file_id(database=test_db) == '0000004'

def test_zeropad():
    assert _zeropad(5,3) == '005'
    assert len(_zeropad(5,3)) == 3

    assert _zeropad(9,9) == '000000009'
    assert len(_zeropad(9,9)) == 9

def test_query_db():
    # NOTE:
    #   The test statement/assertion was commented out
    #       as the acq date-time is from when the file
    #       was created (e.g. in the case of NIFTI files).
    file_id: str = query_db(database=test_db,
                            table='sub_id',
                            prim_key='sub_id',
                            column='file_id',
                            value='CX009902')

    assert file_id == '0000003'

    sub_id: str = query_db(database=test_db,
                            table='sub_id',
                            prim_key='file_id',
                            value=file_id)
    ses_id: str = query_db(database=test_db,
                            table='ses_id',
                            prim_key='file_id',
                            value=file_id)
    acq_date: str = query_db(database=test_db,
                            table='acq_date',
                            prim_key='file_id',
                            value=file_id)
    bids_name: str = query_db(database=test_db,
                            table='bids_name',
                            prim_key='file_id',
                            value=file_id)

    assert sub_id == 'CX009902'
    assert ses_id == 'BMNC000XDF'
    # assert acq_date == '2021-05-31T10:52:50'
    assert bids_name == ''

def test_update_table_row():
    file_id: str = query_db(database=test_db,
                            table='sub_id',
                            prim_key='sub_id',
                            column='file_id',
                            value='CX009902')
    assert file_id == '0000003'

    bids_name: str = query_db(database=test_db,
                            table='bids_name',
                            prim_key='file_id',
                            value=file_id)
    assert bids_name == ''

    update_table_row(database=test_db,
                    prim_key=file_id,
                    table_name='bids_name',
                    value='sub-CX009902_ses-BMNC000XDF_run-01_flair')

    bids_name: str = query_db(database=test_db,
                            table='bids_name',
                            prim_key='file_id',
                            value=file_id)
    assert bids_name == 'sub-CX009902_ses-BMNC000XDF_run-01_flair'

def test_export_bids_scans_dataframe():
    df: pd.DataFrame = export_dataframe(database=test_db)
    assert len(list(df.columns)) == 7
    assert ('acq_date' in list(df.columns)) and ('bids_name' in list(df.columns)) == True

    df: pd.DataFrame = export_scans_dataframe(test_db,
                                            False,
                                            None,
                                            'sub_id',
                                            'ses_id',
                                            'bids_name',
                                            'acq_date')
    assert len(df) == 3
    assert len(list(df.columns)) == 4

    df: pd.DataFrame = _export_tmp_bids_df(database=test_db,
                                        sub_id='CX009902',
                                        modality_type='anat',
                                        modality_label='flair')
    assert len(df) == 1
    assert ('filename' in list(df.columns)) and ('acq_time' in list(df.columns)) == True

    # Construct search dictionary
    [search_dict,
     _,
     _,
     _,
     _] = read_config(config_file=test_config1,
                                   verbose=True)

    df: pd.DataFrame = export_bids_scans_dataframe(database=test_db,
                                                sub_id='CX009902',
                                                search_dict=search_dict)
    assert len(df) == 1
    assert ('filename' in list(df.columns)) and ('acq_time' in list(df.columns)) == True

def test_cleanup():
    """NOTE: This test currently FAILS on Windows operating systems."""
    shutil.rmtree(out_dir)
    assert os.path.exists(out_dir) == False

    shutil.rmtree(dcm_test_data)
    assert os.path.exists(dcm_test_data) == False

    os.remove("dcm2niix")
