# -*- coding: utf-8 -*-
"""Tests for the cs_utils fileio module main classes.
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
    TmpDir,
    File,
    DependencyError,
    Command
)

def test_file_class():
    x: str = 'test.file.txt'
    with File(file=x) as f:
        print (f.file_parts())
        assert f.file == 'test.file.txt'

def test_command_class():
    x: str = 'ls'
    c = Command(x)
    c.cmd_list.append(os.getcwd())
    assert c.check_dependency() == True
    assert c.run() == (0, None, None)

    y: str = 'random_string'
    c = Command(y)
    with pytest.raises(DependencyError):
        assert c.check_dependency() == False

def test_tmpdir_class():
    x: str = 'tmpdir'
    with TmpDir(x,True) as tmp:
        tmp.mk_tmp_dir()
        assert os.path.exists(tmp.tmp_dir) == True
        with TmpDir.TmpFile(tmp.tmp_dir) as f:
            f.touch()
            assert os.path.exists(f.abs_path()) == True
            _ = tmp.rm_tmp_dir(rm_parent=True)
