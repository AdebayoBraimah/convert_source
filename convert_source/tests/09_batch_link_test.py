# -*- coding: utf-8 -*-
"""Tests for convert_source's batch symbolic linking functions.
"""
import pytest

import os
import sys
import pathlib
import platform
import urllib.request
import shutil

from copy import deepcopy
from typing import (
    Dict,
    List
)

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.batch_symlink import (
    batch_link,
    read_file_to_list,
    create_study_sym_links
)
