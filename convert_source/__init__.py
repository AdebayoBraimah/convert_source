# -*- coding: utf-8 -*-
"""Python package used for the conversion of source DICOM, PAR REC, or NIFTI data to raw BIDS NIFTI data.
"""
import os

name: str = "convert_source"
_version_file: str = os.path.abspath(os.path.join(os.path.dirname(__file__),"version.txt"))

with open(_version_file,"r") as f:
    file_contents: str = f.read()
    _cs_version: str = file_contents.strip("\n")
    f.close()

# More information about organizing author information:
# https://stackoverflow.com/questions/1523427/what-is-the-common-header-format-of-python-files
# http://epydoc.sourceforge.net/manual-fields.html#module-metadata-variables

__author__ = "Adebayo Braimah"
__credits__ = ["Adebayo Braimah",
               "Cincinnati Children's Hospital Medical Center", 
               "Imaging Research Center", 
               "CCHMC Dept. of Radiology"]
__license__ = "GPL"
__version__ = _cs_version
__maintainer__ = "Adebayo Braimah"
__email__ = "adebayo.braimah@gmail.com"
__status__ = "Development"
