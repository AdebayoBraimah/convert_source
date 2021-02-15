# -*- coding: utf-8 -*-
"""Python package used for the conversion of source DICOM, PAR REC, or NIFTI data to raw BIDS NIFTI data.
"""

name: str = "convert_source"

import pathlib
import sys
import os

_pkg_path: str = str(pathlib.Path(os.path.abspath(__file__)).parents[1])
sys.path.append(_pkg_path)
_version_file: str = os.path.abspath("version.txt")

from convert_source.cs_utils.utils import file_to_screen

# More on organizing author information:
# https://stackoverflow.com/questions/1523427/what-is-the-common-header-format-of-python-files
# http://epydoc.sourceforge.net/manual-fields.html#module-metadata-variables

__author__ = "Adebayo Braimah"
__credits__ = ["Adebayo Braimah",
               "Cincinnati Children's Hospital Medical Center", 
               "Imaging Research Center", 
               "CCHMC Dept. of Radiology"]
__license__ = "GPL"
__version__ = file_to_screen(_version_file)
__maintainer__ = "Adebayo Braimah"
__email__ = "adebayo.braimah@gmail.com"
__status__ = "Development"
