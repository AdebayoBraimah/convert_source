# -*- coding: utf-8 -*-
"""PAR REC specific functions for convert_source. Primarily intended for converting and renaming PAR REC files to BIDS NIFTI.
"""
import os
import re
import numpy as np
import pandas as pd
from decimal import Decimal
from typing import (
    Optional, 
    Union
)

from convert_source.cs_utils.fileio import TmpDir

# Define exception(s)
class PARfileReadError(Exception):
    pass

# Define function(s)
def get_etl(par_file: str) -> int:
    """Gets EPI factor (Echo Train Length) from Philips' PAR Header.
    
    NOTE: 
        This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Echo Train Length as integer.
    """
    par_file: str = os.path.abspath(par_file)
    regexp: re = re.compile(r'.    EPI factor        <0,1=no EPI>     :   .*?([0-9.-]+)')  # Search string for RegEx
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                etl = match.group(1)
                etl: int = int(etl)
                break
    return etl

def get_wfs(par_file: str) -> float:
    """Gets Water Fat Shift from Philips' PAR Header.
    
    NOTE: 
        This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Water Fat Shift as a float.
    """
    par_file: str = os.path.abspath(par_file)
    regexp: re = re.compile(
        r'.    Water Fat shift \[pixels\]           :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                wfs = match.group(1)
                wfs: float = float(wfs)
                break
    return wfs

def get_red_fact(par_file: str) -> float:
    """Extracts parallel reduction factor in-plane value (SENSE factor) from the file description in the PAR REC header 
    for Philips MR scanners. This reduction factor is assumed to be 1 if a value cannot be found from witin
    the PAR REC header.
    
    NOTE: 
        This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Parallel reduction factor in-plane value (e.g. SENSE factor, as a float).
    """
    
    # Read file
    par_file: str = os.path.abspath(par_file)
    red_fact: str = ""
    regexp: re = re.compile(r' SENSE *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                red_fact = match.group(1)
                red_fact: float = float(red_fact)
                break
    
        if red_fact == "":
            red_fact: float = float(1)
        
    return red_fact

def get_mb(par_file: str) -> int:
    """Extracts multi-band acceleration factor from from Philips' PAR Header.
    
    NOTE: 
        This is done via a regEx search as the PAR header does not normally store this value.
    
    Arguments:
        par_file: Absolute filepath to PAR header file
        
    Returns:
        Multi-band acceleration factor (as an int).
    """
    par_file: str = os.path.abspath(par_file)

    # Initialize mb to 1
    mb: int = 1
    
    regexp: re = re.compile(r' MB *?([0-9.-]+)')
    with open(par_file) as f:
        for line in f:
            match = regexp.search(line)
            if match:
                mb = match.group(1)
                mb: int = int(mb)
                break
    return mb

def get_scan_time(par_file: str) -> Union[float,str]:
    """Gets the acquisition duration (scan time, in s) from the PAR header.
    
    NOTE: 
        This is done via a regEx search as the PAR header is not assumed to change significantly between scanners.
    
    Arguments:
        par_file: PAR header file.
        
    Returns:
        Acquisition duration (scan time, in s). If not in header, an empty string is returned.
    """
    par_file: str = os.path.abspath(par_file)
    scan_time: str = ''
    regexp: re = re.compile(
        r'.    Scan Duration \[sec\]                :   .*?([0-9.-]+)')  # Search string for RegEx, escape the []
    with open(par_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                scan_time = match.group(1)
                scan_time: float = float(scan_time)
                break
    return scan_time

def get_echo_time(par_file: str,
                 tmp_dir: Optional[str] = None
                 ) -> float:
    """Reads the echo time (TE, in sec.) from a PAR header file.

    NOTE: 
        Echo time is obtained from the PAR file header by reading in the PAR header file as a
        pandas dataframe, followed by saving the resulting dataframe as a M x N | N = 35. The echo times
        are stored in the resulting matrix (constructed from numpy as a numpy multi-dimensional array) in 
        row 16 (count starts at 0).
    
    Usage example:
        >>> get_echo_time(par_file="File.PAR")
        88.0
        
    Arguments:
        par_file: PAR header file.
        tmp_dir: Path to temporary directory.
        
    Returns:
        Echo time as a float.
    """
    if tmp_dir:
        pass
    else:
        tmp_dir: str = os.getcwd()
    
    par_file: str = os.path.abspath(par_file)
        
    df: pd.DataFrame = pd.read_csv(par_file,sep="\\s+",skiprows=98)
    df: pd.DataFrame = df.dropna(axis=0)
    
    with TmpDir(tmp_dir=tmp_dir,use_cwd=False) as tmp:
        tmp.mk_tmp_dir()
        with TmpDir.TmpFile(tmp_dir=tmp.tmp_dir,ext="txt") as f:
            df.to_csv(f.file,sep=",",header=False,index=False)
            mat = np.loadtxt(f.file,delimiter=",")
        _ = tmp.rm_tmp_dir(rm_parent=False)
    
    if len(list(np.unique(mat[0:,16]))) > 1:
        raise PARfileReadError(f"Two or more unique echo times were found in {par_file}. Please check.")
    else:
        return float(round(Decimal(float(np.unique(mat[0:,16]))/1000),4))

def get_flip_angle(par_file: str,
                   tmp_dir: Optional[str] = None
                  ) -> float:
    """Reads the flip angle (in degrees) from a PAR header file.

    NOTE: 
        Flip angle is obtained from the PAR file header by reading in the PAR header file as a
        pandas dataframe, followed by saving the resulting dataframe as a M x N | N = 35. The flip angles
        are stored in the resulting matrix (constructed from numpy as a numpy multi-dimensional array) in 
        row 21 (count starts at 0).
    
    Usage example:
        >>> get_flip_angle(par_file="File.PAR")
        90.0
        
    Arguments:
        par_file: PAR header file.
        tmp_dir: Path to temporary directory.
        
    Returns:
        Flip angle as a float.
    """
    if tmp_dir:
        pass
    else:
        tmp_dir: str = os.getcwd()
    
    par_file: str = os.path.abspath(par_file)
        
    df: pd.DataFrame = pd.read_csv(par_file,sep="\\s+",skiprows=98)
    df: pd.DataFrame = df.dropna(axis=0)
    
    with TmpDir(tmp_dir=tmp_dir,use_cwd=False) as tmp:
        tmp.mk_tmp_dir()
        with TmpDir.TmpFile(tmp_file="file.tmp.txt",tmp_dir=tmp.tmp_dir) as f:
            df.to_csv(f.file,sep=",",header=False,index=False)
            mat = np.loadtxt(f.file,delimiter=",")
        _ = tmp.rm_tmp_dir(rm_parent=False)
    
    if len(list(np.unique(mat[0:,21]))) > 1:
        raise PARfileReadError(f"Two or more unique flip angles were found in {par_file}. Please check.")
    else:
        return float(np.unique(mat[0:,21]))
