# -*- coding: utf-8 -*-
"""Command line wrapper for `convert_source`'s study directory symlink functions. 
   Performs symlinking for a study's subject imaging data.
"""
import pathlib
import sys
import os

from shutil import copyfile
from datetime import datetime
from typing import (
    List,
    Optional
)

_pkg_path: str = str(
    pathlib.Path(
        os.path.abspath(__file__)
            ).parents[2])

sys.path.append(_pkg_path)

from convert_source.cs_utils.fileio import LogFile

link_version = '0.0.1'

def batch_link(study_dir: str,
                infile: str,
                mapfile: str,
                out_dir: str
                ) -> List[str]:
    """Batch function for symbolic linking child subject directories that contain imaging data.
    The parent directory is assumed to be the study directory that contains all subjects.

    Usage example:
        >>> sym_link_dirs = batch_link(study_dir='/<parent>/<dir>',
        ...                            infile='dir_names.txt',
        ...                            mapfile='bids_names.txt',
        ...                            out_dir='/<bids>/<outdir>')
        ...

    Arguments:
        study_dir: Parent study directory.
        infile: Input file that contains the names of the child directories to be sym-linked.
        mapfile: Input file that contains the names to be mapped to.
        out_dir: Output directory (need not exist at runtime).

    Returns:
        List of sym-linked subject child directories.
    """
    study_dir: str = os.path.abspath(study_dir)

    # Write logs
    misc_dir: str = os.path.join(out_dir,'.misc')
    if os.path.exists(misc_dir):
        out_dir: str = os.path.abspath(out_dir)
        misc_dir: str = os.path.abspath(misc_dir)
    else:
        os.makedirs(misc_dir)
        misc_dir: str = os.path.abspath(misc_dir)
        out_dir: str = os.path.abspath(out_dir)
    
    now = datetime.now()
    dt_string: str = str(now.strftime("%m_%d_%Y_%H_%M"))

    _log: str = os.path.join(misc_dir,f"prep_study_{dt_string}.log")
    log: LogFile = log_file(log=_log)

    copyfile(infile, os.path.join(misc_dir,'orig_subject_id.txt'))
    copyfile(mapfile, os.path.join(misc_dir,'map_subject_id.txt'))

    sym_list: List[str] = create_study_sym_links(study_dir=study_dir,
                                                 infile=infile,
                                                 mapfile=mapfile,
                                                 outdir=out_dir,
                                                 log_file=log)
    return sym_list

# Functions for symlink creation
def read_file_to_list(file: str) -> List[str]:
    """Opens the (text) file, reads its contents, and stores those contents in a list of strings. 
    Should the input file not exist, then the text is assumed to be a string and is returned instead.
    
    Usage example:
        >>> contents = read_file_to_list(file="filename.txt")
        >>> contents
        ["index_1", "index_2", "index_3"]
    
    Arguments:
        file: Input file or string.
        
    Returns:
        List of strings of the file contents
    """
    if os.path.exists(file) and os.path.isfile(file):
        file: str = os.path.realpath(file)
        with open(file, "r") as file:
            lines: List[str] = file.readlines()
            lines: List[str] = [ x.replace('\n','') for x in lines ]
            file.close()
    else:
        lines: List[str] = [file]
    return lines

def create_study_sym_links(study_dir: str,
                           infile: str,
                           mapfile: str,
                           outdir: str,
                           log_file: Optional[LogFile] = None
                          ) -> List[str]:
    """Creates another study directory of sym-linked subject directories to the original study directory.
    The input file contains the directory names of subjects in the study directory. The corresponding map 
    file contains the subject IDs to be mapped to.
    
    Usage example:
        >>> dir_list  = create_study_sym_links(study_dir="input_dir",
        ...                                    infile="file1.txt", 
        ...                                    mapfile="file2.txt", 
        ...                                    outdir="NewDirectory")
        ...
    
    Arguments:
        study_dir: Input parent study directory that contains each subjects' imaging data.
        infile: Input file of directories to be mapped.
        mapfile: Corresponding file that contains the subject directories to be mapped to.
        outdir: Output directory for all symlinked directories.
        log_file: LogFile object for logging.
    
    Returns:
        List of sym-linked directories.
        
    Raises:
        IndexError is raised if the number of entries in ``infile`` and ``mapfile`` are not equal.
    """
    study_dir: str = os.path.abspath(study_dir)

    if log_file:
        log_file.log("Symbollically linking subject data directories.")
        log_file.log(f"Performed using: prep_study v{link_version}")
        log_file.log(f"Input study directory: {study_dir}")
        log_file.log(f"Output symbolic link directory: {outdir} \n")

    if os.path.exists(outdir):
        outdir: str = os.path.abspath(outdir)
    else:
        os.makedirs(outdir)
        outdir: str = os.path.abspath(outdir)
    
    infile: str = os.path.realpath(infile)
    mapfile: str = os.path.realpath(mapfile)
    
    img_dirs: List[str] = read_file_to_list(file=infile)
    target_dirs: List[str] = read_file_to_list(file=mapfile)
    
    if len(img_dirs) == len(target_dirs):
        pass
    else:
        if log_file:
            log_file.error(f"Input lists from {infile} and {mapfile} are of different lengths.")
        raise IndexError(f"Input lists from {infile} and {mapfile} are of different lengths.")
    
    dir_list: List[str] = []

    for i,j in zip(img_dirs,target_dirs):
        sub_dir: str = os.path.join(study_dir,i)
        tar_dir: str = os.path.join(outdir,j)

        if os.path.exists(tar_dir) and os.path.islink(tar_dir):
            if log_file:
                log_file.log(f"(Symbolically linked) directory already exists: {i} -> {j}.")
        elif os.path.exists(tar_dir):
            if log_file:
                log_file.log(f"This directory already exists and is likely not a symbolically linked directory.")   
        else:
            if log_file:
                log_file.log(f"Symbollically linked directories: {i} -> {j}.")
            os.symlink(sub_dir,tar_dir)
        dir_list.append(tar_dir)
    return dir_list

def log_file(log: str) -> LogFile:
    """Initializes log file object for logging purposes.

    Usage example:
        >>> logger = log(log_file)
        >>>
        >>> logger.info("Some information")
        >>> logger.warning("Some warning")
        
    Arguments:
        log: Log file name.

    Returns:
        LogFile object to be logged to.
    """
    log: LogFile = LogFile(log_file=log)

    now = datetime.now()
    dt_string = now.strftime("%A %B %d, %Y %H:%M:%S")

    log.info(dt_string)
    log.info(f"prep_study v{link_version}")

    return log
