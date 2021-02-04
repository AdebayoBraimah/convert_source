# -*- coding: utf-8 -*-
"""Tests for the imgio's pario module's functions.
"""
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

from convert_source.cs_utils.fileio import (
    Command,
    DependencyError
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info
)

# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)