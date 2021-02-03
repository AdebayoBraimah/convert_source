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

# from convert_source.cs_utils.utils import (
#     # imports
# )
# 
# from convert_source.imgio.dcmio import (
#     # imports
# )

# Windows commands
# 
# Unzip on windows command line (windows 10): tar -xf <file.zip>
# 
# Recursively remove directories (and files, PowerShell): Remove-Item <directory> -Recurse
# Recursively remove directories (and files, cmd): del /s /q /f <directory>
# Recursively remove directories (and files, cmd): rmdir /s /q /f <directory>

# Test variables
scripts_dir: str = os.path.join(os.getcwd(),'TEST001-UNIT001','data.dicom')
tmp_out: str = os.path.join(os.getcwd(),'tmp.subs.dir')
tmp_json: str = os.path.join(scripts_dir,'test.orig.json')