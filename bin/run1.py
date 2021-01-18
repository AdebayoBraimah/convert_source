#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-

'''
TODO:
    - Enable gzipping/gunzipping utility function(s) for cases when interacting with 
        uncompressed image files.
            - Or in the case the desired output files need to be uncompressed.  
'''

from utils.command_utils import Command, DependencyError

def batch_convert():

    # Read configurations file, and define search terms
    # iterate through parent directory, and get subject IDs and session IDs
    # search, find, and categorize image data for each subject and each session


def convert_image_data(file: str,
                       basename: str,
                       out_dir: str,
                       cprss_lvl: int = 6,
                       bids: bool = True,
                       anon_bids: bool = True,
                       gzip: bool = True,
                       comment: bool = True,
                       adjacent: bool = False,
                       dir_search: int = 5,
                       nrrd: bool = False,
                       ignore_2D: bool = True,
                       merge_2D: bool = True,
                       text: bool = False,
                       progress: bool = False,
                       verbose: bool = False,
                       write_conflicts: str = "suffix",
                       crop_3D: bool = False,
                       lossless: bool = False,
                       big_endian: str = "optimal",
                       xml: bool = False):
    '''Converts raw image data (DICOM, PAR REC, or Bruker) to NifTi (or NRRD) using dcm2niix.
    This is a wrapper function for dcm2niix (v1.0.20190902+). This wrapper functions has no returns, 
    however output files are generated in a specified directory that must exist prior to the 
    invokation of this function.

    * TODO:
        - Use TmpDir class to create temporary directory and files. Copy files to target output directory.
    
    Note: Most of the defaults for dcm2niix have been preserved aside from those starred (*) in the
    (optional) arguments section, in order to be BIDS compliant.

    Arguments (Required):
        file (string): Absolute path to raw image data file
        basename (string): Output file(s) basename
        out_dir (string): Absolute path to output directory (must exist at runtime)

    Arguments (Optional):
        cprss_lvl (int): Compression level [1 - 9] - 1 is fastest, 9 is smallest (default: 6)
        bids (bool): BIDS (JSON) sidecar (default: True) * 
        anon_bids (bool): Anonymize BIDS (default: True) * 
        gzip (bool): Gzip compress images (default: True) *
        comment (bool): Image comment(s) stored in NifTi header (default: True) *
        adjacent (bool): Assumes adjacent DICOMs/Image data (images from same series always in same folder) for faster conversion (default: False)
        dir_search (int): Directory search depth (default: 5)
        nrrd (bool): Export as NRRD instead of NifTi, not recommended (default: False)
        ignore_2D (bool): Ignore derived, localizer and 2D images (default: True)
        merge_2D (bool): Merge 2D slices from same series regardless of echo, exposure, etc. (default: True)
        text (bool): Text notes includes private patient details in separate text file (default: False)
        progress (bool): Report progress, slicer format progress information (default: True)
        verbose (bool): Enable verbosity (default: False)
        write_conflicts (string): Write behavior for name conflicts:
            - 'suffix' = Add suffix to name conflict (default)
            - 'overwrite' = Overwrite name conflict
            - 'skip' = Skip name conflict
        crop_3D (bool): crop 3D acquisitions (default: False)
        lossless (bool): Losslessly scale 16-bit integers to use dynamic range (default: True)
        big_endian (string): Byte order:
            - 'optimal' or 'native' = optimal/native byte order (default)
            - 'little-end' = little endian
            - 'big-end' = big endian
        xml (bool): Slicer format features (default: False)
        
        Returns:
            None
    '''

    # Empty list
    conv_cmd = list()

    # Get OS platform
    if platform.system().lower() == 'windows':
        conv_cmd.append("dcm2niix.exe")
    else:
        conv_cmd.append("dcm2niix")

    # Boolean True/False options arrays
    bool_opts = [bids, anon_bids, gzip, comment, adjacent, nrrd, ignore_2D, merge_2D, text, verbose, lossless, progress, xml]
    bool_vars = ["-b", "-ba", "-z", "-c", "-a", "-e", "-i", "-m", "-t", "-v", "-l", "--progress", "--xml"]

    # Initial option(s)
    if cprss_lvl:
        conv_cmd.append(f"-{cprss_lvl}")

    # Keyword option(s)
    if write_conflicts.lower() == "suffix":
        conv_cmd.append("-w")
        conv_cmd.append("2")
    elif write_conflicts.lower() == "overwrite":
        conv_cmd.append("-w")
        conv_cmd.append("1")
    elif write_conflicts.lower() == "skip":
        conv_cmd.append("-w")
        conv_cmd.append("0")

    # if big_endian.lower() == "optimal" or big_endian.lower() == "native":
    #     conv_cmd.append("--big_endian")
    #     conv_cmd.append("o")
    # elif big_endian.lower() == "little-end":
    #     conv_cmd.append("--big_endian")
    #     conv_cmd.append("n")
    # elif big_endian.lower() == "big-end":
    #     conv_cmd.append("--big_endian")
    #     conv_cmd.append("y")


    for idx,var in enumerate(bool_opts):
        if var:
            conv_cmd.append(bool_vars[idx])
            conv_cmd.append("y")

    # Required arguments
    # Filename
    conv_cmd.append("-f")
    conv_cmd.append(f"{basename}")

    # Output directory
    conv_cmd.append("-o")
    conv_cmd.append(f"{out_dir}")

    # Image file   
    conv_cmd.append(f"{file}")

    # System Call to dcm2niix (assumes dcm2niix is added to system path variable)
    subprocess.call(conv_cmd)

    return None