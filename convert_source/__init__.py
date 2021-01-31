# -*- coding: utf-8 -*-

name: str = "convert_source"

import pathlib
import sys
import os

pkg_path: str = str(pathlib.Path(os.path.abspath(__file__)).parents[1])
sys.path.append(pkg_path)
