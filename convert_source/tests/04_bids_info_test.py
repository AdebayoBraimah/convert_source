# -*- coding: utf-8 -*-
"""Tests for the `bids_info` module's functions.
"""

import pytest

import os
import sys
import pathlib

from typing import Dict

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.bids_info import (
    is_camel_case,
    construct_bids_dict,
    construct_bids_name
)

from convert_source.cs_utils.const import (
    BIDS_INFO,
    BIDS_ORD_ARR
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    depth
)

def test_is_camel_case():
    assert is_camel_case("CamelCase",bids_case=False) == True
    assert is_camel_case("CamelCase",bids_case=True) == True
    assert is_camel_case("camelCase",bids_case=False) == True
    assert is_camel_case("camelCase",bids_case=True) == False
    assert is_camel_case("camelcase",bids_case=False) == False
    assert is_camel_case("camelcase",bids_case=True) == False

def test_construct_bids_dict():
    bids_meta_dict: Dict = construct_bids_dict()
    assert depth(bids_meta_dict) == 2
    assert bids_meta_dict != BIDS_INFO
    assert list(bids_meta_dict.keys()) != BIDS_ORD_ARR

def test_construct_bids_name():
    sub: SubDataInfo = SubDataInfo('001','.')
    bids_name_dict: Dict[str] = construct_bids_name(sub)
    assert depth(bids_name_dict) == 4
    assert bids_name_dict['unknown'].get('modality_label','') == 'unknown'
