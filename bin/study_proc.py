#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc-string
"""

import pathlib
import sys
import os

import argparse

_pkg_path: str = str(pathlib.Path(os.path.abspath(__file__)).parents[1])
sys.path.append(_pkg_path)

# from convert_source import __version__ as version
# print(version)

from convert_source.batch_convert import batch_proc

def parser():
    '''
    working doc-string
    '''
    




