# -*- coding: utf-8 -*-
"""File utility functions for convert_source.
"""


# Import packages and modules
import json
from json import JSONDecodeError
import os
from shutil import copy
import glob
# import subprocess
import gzip
import numpy as np
import platform
from typing import (
    List, 
    Dict, 
    Optional, 
    Union, 
    Tuple
)

# Import third party packages and modules
import convert_source_dcm as cdm
import convert_source_par as csp

from utils.command_utils import ( 
    Command, 
    DependencyError, 
    ConversionError, 
    TmpDir, 
    LogFile, 
    File, 
    NiiFile
)

# Define functions

def file_to_screen(file: str) -> str:
    '''Reads the contents of a file and prints it to screen.

    Arguments:
        file: Path to file.

    Returns:
        File contents returned as string, printed to screen.
    '''

    with open(file,"r") as f:
        file_contents = f.read()
        f.close()
    return file_contents

def get_echo(json_file: str) -> float:
    '''Reads the echo time (TE) from the NIFTI JSON sidecar and returns it.

    Arguments:
        json_file (string): Absolute path to JSON sidecar.

    Returns:
        Echo time as a float.
    '''

    with open(json_file, "r") as read_file:
        data = json.load(read_file)
    echo = data.get("EchoTime")
    return echo

def get_num_runs(out_dir,scan,ses="",task="",acq="",ce="",dirs="",rec="",echo=""):
    '''

    * This should use a dictionary - update function later *

    Determines run number of a scan (e.g. T1w, T2w, bold, dwi etc.) in an output directory by globbing the 
    directory for the number of NifTis of the same scan.

    Arguments (required):
        out_dir (string): Absolute path to output directory
        scan (string): Modality (e.g. T1w, T2w, bold, dwi, etc.)

    Arguments (optional):
        ses (string): Session ID
        task (string): Task ID
        acq (string): Acquisition ID
        ce (string): Contrast Enhanced ID
        dirs (string): Directions ID string
        rec (string): Reconstruction algorithm string
        echo (int or string): Echo number from multi-echo functional scan

    Returns:
        run_num (int): Returns the run number for the specific scan
    '''

    runs = os.path.join(out_dir, f"*{ses}*{task}*{acq}*{ce}*{dirs}*{rec}*{echo}*{scan}*.nii*")
    run_num = len(glob.glob(runs))
    run_num = run_num + 1

    return run_num

# This is implemented in command_utils
# def file_parts(file):
#     '''
#     Divides file with file path into: path, filename, extension.
    
#     Arguments:
#         file (string): File with absolute filepath
        
#     Returns: 
#         path (string): Path of input file
#         filename (string): Filename of input file, without the extension
#         ext (string): Extension of input file
#     '''
    
#     [path, file_with_ext] = os.path.split(file)
    
#     # Make condition for gzipped files
#     if '.gz' in file_with_ext:
#         file_with_ext = file_with_ext[:-3]
#         [filename,ext] = os.path.splitext(file_with_ext)
#         ext = ext + '.gz'
#     else:
#         [filename,ext] = os.path.splitext(file_with_ext)
    
#     path = str(path)
#     filename = str(filename)
#     ext = str(ext)
    
#     return path,filename,ext

def gzip_file(file: str,
              native: bool = True
              ) -> str:
    '''Gzips file. Native implementation of gzipping files is prefered with
    this function provided that the system is UNIX. Otherwise, a pythonic 
    implementation of gzipping is performed.
    
    Arguments:
        file: Input file.
        native: Uses native implementation of gzip.
        
    Returns: 
        Gzipped file.
    '''

    # Check if native method was enabled.
    if native:
        if platform.system().lower() == 'windows':
            native = False
        else:
            native = True
    
    if native:
        # Native implementation
        file: File = File(file)
        [ path, filename, ext ] = file.file_parts()
        out_file: str = os.path.join(path,filename + ext + '.gz')
        gzip_cmd: Command = Command("gzip")
        gzip_cmd.cmd_list.append(file.file)
        gzip_cmd.cmd_list.append(out_file)
        gzip_cmd.run()
        return out_file
    else:
        # Define tempory file for I/O buffer stream
        tmp_file: File = File(file)
        [ path, filename, ext ] = tmp_file.file_parts()
        out_file: str = os.path.join(path,filename + ext + '.gz')
        
        # Pythonic gzip
        with open(file,"rb") as in_file:
            data = in_file.read(); in_file.close()
            with gzip.GzipFile(out_file,"wb") as tmp_out:
                tmp_out.write(data)
                tmp_out.close()
                os.remove(file) 
        return out_file

def gunzip_file(file: str,
                native: bool = True
                ) -> str:
    '''Gunzips file. Native implementation of gunzipping files is prefered with
    this function provided that the system is UNIX. Otherwise, a pythonic 
    implementation of gunzipping is performed.
    
    Arguments:
        file: Input file.
        native: Uses native implementation of gunzip.
        
    Returns: 
        Gunzipped file.
    '''

    # Check if native method was enabled.
    if native:
        if platform.system().lower() == 'windows':
            native = False
        else:
            native = True
    
    if native:
        # Native implementation
        file: File = File(file)
        [ path, filename, ext ] = file.file_parts()
        out_file: str = os.path.join(path,filename + ext[:-3])
        gunzip_cmd: Command = Command("gunzip")
        gunzip_cmd.cmd_list.append(file.file)
        gunzip_cmd.cmd_list.append(out_file)
        gunzip_cmd.run()
        return out_file
    else:
        # Define tempory file for I/O buffer stream
        tmp_file: File = File(file)
        [ path, filename, ext ] = tmp_file.file_parts()
        out_file: str = os.path.join(path,filename + ext[:-3])
        
        # Pythonic gunzip
        with gzip.GzipFile(file,"rb") as in_file:
            data = in_file.read(); in_file.close()
            with open(out_file,"wb") as tmp_out:
                tmp_out.write(data)
                tmp_out.close()
                os.remove(file)
        return out_file

def read_json(json_file: str) -> Dict:
    '''Reads JavaScript Object Notation (JSON) file.
    
    Arguments:
        json_file: Input file.
        
    Returns: 
        Dictionary of key mapped items from JSON file.
    '''
    
    # Read JSON file
    if json_file:
        with open(json_file) as file:
            return json.load(file)
    else:
        return dict()

def update_json(json_file: str,
                dictionary: Dict
                ) -> str:
    '''Updates JavaScript Object Notation (JSON) file. If the file does not exist, it is created once
    this function is called.
    
    Arguments:
        json_file: Input file.
        dictionary: Dictionary of key mapped items to write to JSON file.
        
    Returns: 
        Updated JSON file.
    '''
    
    # Check if JSON file exists, if not, then create JSON file
    if not os.path.exists(json_file):
        with open(json_file,"w"): pass

    # Read JSON file
    data_orig: Dict = read_json(json_file)
        
    # Update original data from JSON file
    data_orig.update(dictionary)
    
    # Write updated JSON file
    with open(json_file,"w") as file:
        json.dump(data_orig,file,indent=4)
    
    return json_file

def dict_multi_update(dictionary: Optional[Dict] = None,
                      **kwargs
                      ) -> Dict:
    '''Updates a dictionary multiple times depending on the number key word mapped pairs that are provided and 
    returns a separate updated dictionary. The dictionary passed as an argument need not exist at runtime.
    
    Example usage:
        >>> new_dict = dict_multi_update(old_dict,
        ...                              Manufacturer="Philips",
        ...                              ManufacturersModelName="Ingenia",
        ...                              MagneticFieldStrength=3,
        ...                              InstitutionName="CCHMC")
    
    Arguments:
        dictionary: Dictionary of key mapped items to write to JSON file.
        **kwargs: key=value pairs.
        
    Returns: 
        New updated dictionary.
    '''
    
    # Create new dictionary
    if dictionary:
        new_dict: Dict = dictionary.copy()
    else:
        new_dict: Dict = {}
    
    for key,item in kwargs.items():
        tmp_dict: Dict = {key:item}
        new_dict.update(tmp_dict)
    
    return new_dict

def get_bvals(bval_file: str) -> List[float]:
    '''Reads the bvals from the (FSL-style) bvalue file and returns a list of unique non-zero bvalues
    
    Arguments:
        bval_file: Bval (.bval) file.
        
    Returns: 
        List of unique, non-zero bvalues (as floats).
    '''
    bval_file: str = os.path.abspath(bval_file)
    vals = np.loadtxt(bval_file)
    vals_nonzero = vals[vals.astype(bool)]
    return list(np.unique(vals_nonzero))

def get_metadata(dictionary: Optional[Dict] = None,
                 scan_type: Optional [str] = None,
                 task: Optional[str] = None
                 ) -> Tuple[Dict,Dict]:
    '''Reads the metadata dictionary and looks for keywords to indicate what metadata should be written to which
    dictionary. For example, the keyword 'common' is used to indicate the common information for the imaging
    protocol and may contain information such as: field strength, phase encoding direction, institution name, etc.
    Additional keywords that are BIDS sub-directories names (e.g. anat, func, dwi) will return an additional
    dictionary which contains metadata specific for those modalities. Func also has additional keywords based on
    the task specified. If an empty dictionary is passed as an argument, then this function returns empty dictionaries
    as a result.
    
    Arguments:
        dictionary: Nested dictionary of key mapped items from the 'read_config' function.
        scan_type: BIDS scan type (e.g. anat, func, dwi, etc.).
        task: Task name to search in the key mapped dictionary.
        
    Returns:
        Tuple of dictionaries that contain:
            - Common metadata dictionary.
            - Modality specific metadata dictionaries.
    '''

    if dictionary:
        pass
    else:
        dictionary: Dict = {}
    
    # Create empty dictionaries
    com_param_dict: Dict = {}
    scan_param_dict: Dict = {}
    scan_task_dict: Dict = {}
    
    # Iterate through, looking for key words (e.g. common and scan_type)
    for key,item in dictionary.items():
        # BIDS common metadata fields (normally shared by all modalities)
        if key.lower() in 'common':
            com_param_dict = dictionary[key]

        # BIDS modality specific metadata fields
        if key.lower() in scan_type:
            scan_param_dict = dictionary[key]
            if task.lower() in scan_param_dict:
                for dict_key,dict_item in scan_param_dict.items():
                    if task.lower() in dict_key:
                        scan_task_dict = scan_param_dict[dict_key]
                        
        if len(scan_task_dict) != 0:
            scan_param_dict = scan_task_dict
    
    return com_param_dict, scan_param_dict

def list_in_substr(in_list: List[str],
                   in_str: str
                   ) -> bool:
    '''Searches a string using a list that contains substrings. Returns boolean 'True' or 'False' 
    if any elements of the list are found within the string.
    
    Example usage:
        >>> list_in_substr('['T1','TFE']','sub_T1_image_file')
        True
        >>> 
        >>> list_in_substr('['T2','TSE']','sub_T1_image_file')
        False
    
    Arguments:
        in_list: List containing strings used for matching.
        in_str: Larger string to be searched for matches within substring.
    
    Returns: 
        boolean True or False.
    '''

    for word in in_list:
        if any(word.lower() in in_str.lower() for element in in_str.lower()):
            return True
        else:
            return False

class BIDSimg():
    '''File collection and organization object intended for handling 
    Brain Imaging Data Structure (BIDS) data in the processing of being converted from source data to 
    NIFTI.
    
    Attributes:
        imgs: List of NIFTI files.
        jsons: Corresponding list of JSON sidecar(s).
        bvals: Corresponding list of bval file(s).
        bvecs: Corresponding list of bvec file(s).
    '''

    def __init__(self,
                 work_dir: str):
        '''Constructs class instance lists for NIFTI, JSON, bval, and bvec files.
        
        Arguments:
            work_dir: Input working directory that contains the image files and 
                their associated output files.
        '''
        # Working directory
        self.work_dir: str = os.path.abspath(work_dir)

        # Init empty lists
        self.imgs: List[str] = []
        self.jsons: List[str] = []
        self.bvals: List[str] = []
        self.bvecs: List[str] = []
            
        # Find, organize, and sort NIFTI files
        search_dir: str = os.path.join(self.work_dir,"*.nii*")
        imgs: List[str] = glob.glob(search_dir)
        self.imgs: List[str] = imgs
        self.imgs.sort(reverse=False)
        del search_dir, imgs

        # Find and organize associated JSON, bval & bvec files
        for img in self.imgs:
            img_file: NiiFile = NiiFile(img)
            [path, file, ext] = img_file.file_parts()

            json: str = os.path.join(path,file + ".json")
            bval: str = os.path.join(path,file + ".bval")
            bvec: str = os.path.join(path,file + ".bvec")

            # JSON
            if os.path.exists(json):
                self.jsons.append(json)
            else:
                self.jsons.append("")
            
            # bval
            if os.path.exists(bval):
                self.bvals.append(bval)
            else:
                self.bvals.append("")
            
            # bvec
            if os.path.exists(bvec):
                self.bvecs.append(bvec)
            else:
                self.bvecs.append("")

            del img_file,path,file,ext,json,bval,bvec
    
    def __repr__(self):
        '''NOTE: Returns a string represented as a dictionary of list items.'''
        return ( str({"imgs": self.imgs,
                      "jsons": self.jsons,
                      "bvals": self.bvals,
                      "bvecs": self.bvecs}) )
    
    def copy_img_data(self,
                      target_dir: str
                     ) -> Tuple[List[str],List[str],List[str],List[str]]:
        '''Copies image data and their associated files to some target directory.

        NOTE: This function resets the class attributes of the class instance with the
            returns of this function.
        
        Arguments:
            target_dir: Target directory to copy files to.
            
        Returns:
            Tuple of four lists of strings that correspond to:
                - NIFTI image files
                - Corresponding JSON file(s)
                - Corresponding bval file(s)
                - Corresponding bvec file(s)
        '''
        
        # Init new lists
        imgs: List[str] = self.imgs
        jsons: List[str] = self.jsons
        bvals: List[str] = self.bvals
        bvecs: List[str] = self.bvecs
            
        # Clear class (public) list attributes
        self.imgs: List[str] = []
        self.jsons: List[str] = []
        self.bvals: List[str] = []
        self.bvecs: List[str] = []
        
        # Copy image files
        for img in imgs:
            file = copy(img,target_dir)
            self.imgs.append(file)
            
        # Copy JSON files
        for json in jsons:
            try:
                file = copy(json,target_dir)
                self.jsons.append(file)
            except FileNotFoundError:
                self.jsons.append("")
                
            
        # Copy bval files
        for bval in bvals:
            try:
                file = copy(bval,target_dir)
                self.bvals.append(file)
            except FileNotFoundError:
                self.bvals.append("")
        
        # Copy bvec files
        for bvec in bvecs:
            try:
                file = copy(bvec,target_dir)
                self.bvecs.append(file)
            except FileNotFoundError:
                self.bvecs.append("")
        
        return self.imgs, self.jsons, self.bvals, self.bvecs

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
                       progress: bool = True,
                       verbose: bool = False,
                       write_conflicts: str = "suffix",
                       crop_3D: bool = False,
                       lossless: bool = False,
                       big_endian: str = "o",
                       xml: bool = False,
                       log: Optional[LogFile] = None,
                       env: Optional[Dict] = None,
                       dryrun: bool = False
                       ) -> BIDSimg:
                    #   ) -> Tuple[List[str],List[str],List[str],List[str]]:
    '''Converts medical image data (DICOM, PAR REC, or Bruker) to NifTi (or NRRD) using dcm2niix.
    This is a wrapper function for dcm2niix (v1.0.20190902+).

    Usage example:
        >>> data = convert_image_data("IM00001.dcm",
        ...                           "img0001",
        ...                           "<path/to/out/directory>")
        >>> data.imgs[0]
        "<path/to/image.nii>"
        >>>
        >>> data.jsons[0]
        "<path/to/image.json>"
        >>>
        >>> data.bvals[0]
        "<path/to/image.bval>"
        >>>
        >>> data.bvecs[0]
        "<path/to/image.bvec>"

    Arguments:
        file: Absolute path to raw image data file.
        basename: Output file(s) basename.
        out_dir: Absolute path to output directory (must exist at runtime).
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest (default: 6).
        bids: BIDS (JSON) sidecar (default: True).
        anon_bids: Anonymize BIDS (default: True).
        gzip: Gzip compress images (default: True).
        comment: Image comment(s) stored in NifTi header (default: True).
        adjacent: Assumes adjacent DICOMs/Image data (images from same series always in same folder) for faster conversion (default: False).
        dir_search (int): Directory search depth (default: 5).
        nrrd: Export as NRRD instead of NifTi, not recommended (default: False).
        ignore_2D: Ignore derived, localizer and 2D images (default: True).
        merge_2D: Merge 2D slices from same series regardless of echo, exposure, etc. (default: True).
        text: Text notes includes private patient details in separate text file (default: False).
        progress: Report progress, slicer format progress information (default: True).
        verbose: Enable verbosity (default: False).
        write_conflicts: Write behavior for name conflicts:
            - 'suffix' = Add suffix to name conflict (default)
            - 'overwrite' = Overwrite name conflict
            - 'skip' = Skip name conflict
        crop_3D: crop 3D acquisitions (default: False).
        lossless: Losslessly scale 16-bit integers to use dynamic range (default: True).
        big_endian: Byte order:
            - 'o' = optimal/native byte order (default)
            - 'n' = little endian
            - 'y' = big endian
        xml: Slicer format features (default: False).
        log: LogFile object for logging.
        env: Path environment dictionary.
        dryrun: Perform dryrun (creates the command, but does not execute it).
        
    Returns:
        BIDSimg data object that contains:
            - imgs: List of NIFTI image files
            - jsons: Corresponding list of JSON file(s)
            - bvals: Corresponding bval file(s)
            - bvecs: Corresponding bvec file(s)

        * Tuple of four lists of strings that correspond to: *
            - NIFTI image files
            - Corresponding JSON file(s)
            - Corresponding bval file(s)
            - Corresponding bvec file(s)
    
    Raises:
        ConversionError: Error that arises if no converted (NIFTI) images are created.
    '''
    
    # Get OS platform and construct command line args
    if platform.system().lower() == 'windows':
        convert: Command = Command("dcm2niix.exe")
    else:
        convert: Command = Command("dcm2niix")

    # Boolean True/False options arrays
    bool_opts: List[Union[str,bool]] = [bids, anon_bids, gzip, comment, adjacent, nrrd, ignore_2D, merge_2D, text, verbose, lossless, progress, xml]
    bool_vars: List[str] = ["-b", "-ba", "-z", "-c", "-a", "-e", "-i", "-m", "-t", "-v", "-l", "--progress", "--xml"]

    # Initial option(s)
    if cprss_lvl:
        convert.cmd_list.append(f"-{cprss_lvl}")

    # Keyword option(s)
    if write_conflicts.lower() == "suffix":
        convert.cmd_list.append("-w")
        convert.cmd_list.append("2")
    elif write_conflicts.lower() == "overwrite":
        convert.cmd_list.append("-w")
        convert.cmd_list.append("1")
    elif write_conflicts.lower() == "skip":
        convert.cmd_list.append("-w")
        convert.cmd_list.append("0")
    
    if big_endian.lower() == "o":
        convert.cmd_list.append("--big_endian")
        convert.cmd_list.append("o")
    elif big_endian.lower() == "n":
        convert.cmd_list.append("--big_endian")
        convert.cmd_list.append("n")
    elif big_endian.lower() == "y":
        convert.cmd_list.append("--big_endian")
        convert.cmd_list.append("y")
    
    for opt in zip(bool_opts,bool_vars):
        if opt[0]:
            convert.cmd_list.append(opt[1])
            convert.cmd_list.append("y")

    # Output filename
    convert.cmd_list.append("-f")
    convert.cmd_list.append(f"{basename}")

    # Create TmpDir object
    with TmpDir(tmp_dir=out_dir,use_cwd=False) as tmp_dir:
        # Create temporary output directory
        tmp_dir.mk_tmp_dir()
        
        # Output directory
        out_dir: str = os.path.abspath(out_dir)

        convert.cmd_list.append("-o")
        convert.cmd_list.append(f"{tmp_dir.tmp_dir}")

        # Image file   
        convert.cmd_list.append(f"{file}")
        
        # Execute command
        convert.run(log=log,env=env,dryrun=dryrun)
        
        # Copy files to output directory
        img_data: BIDSimg = BIDSimg(work_dir=tmp_dir.tmp_dir)
        [imgs, jsons, bvals, bvecs] = img_data.copy_img_data(target_dir=out_dir)
        
        # Clean-up
        tmp_dir.rm_tmp_dir(rm_parent=False)
    
    # Image file check
    if len(imgs) == 0:
        raise ConversionError("Image conversion error. No output images were found.")

    # return imgs, jsons, bvals, bvecs
    return img_data

# def cp_file(file: str,
#             work_dir: Optional[str] = None,
#             work_name: Optional[str] = None
#             ) -> str:
#     '''Copies a file. Primarily intended for copying single file image data.
    
#     Arguments:
#         file (string): File path to source (image) file
#         work_dir (string): Absolute path to working directory (must exist at runtime prior to invoakation of this function). If left empty, then the directory of the source file is used.
#         work_name (string): Output name for (image) file. If left empty, the output name is the same as the source file.
        
#     Returns:
#         out_file (string): Absolute path to output file.
#     '''
    
#     [file: File = File(file)
#     [ path, filename, ext ] = file.file_parts()
    
#     if work_dir == "":
#         work_dir = path
#     else:
#         work_dir = os.path.abspath(work_dir)
        
#     if work_name == "":
#         work_name = filename
        
#     out_file = os.path.join(work_dir,work_name + ext)
    
#     shutil.copy(file,out_file)
    
#     return out_file

def get_recon_mat(json_file: str) -> Union[float,str]:
    '''Reads ReconMatrixPE (reconstruction matrix phase encode) value from the JSON sidecar.
    
    Arguments:
        json_file: BIDS JSON file.
        
    Returns:
        Recon Matrix PE value (as a float if it exists in the file, or as a string if not in the file).
    '''

    json_file: str = os.path.abspath(json_file)
    
    # Read JSON file
    try:
        with open(json_file, "r") as read_file:
            data: Dict = json.load(read_file)
            return data["ReconMatrixPE"]
    except JSONDecodeError:
        pass 
        return 'unknown'

def get_pix_band(json_file: str) -> Union[float,str]:
    '''Reads pixel bandwidth value from the JSON sidecar.
    
    Arguments:
        json_file (string): BIDS JSON file.
        
    Returns:
        Pixel bandwidth value (as a float if it exists in the file, or as a string if not in the file).
    '''
    
    json_file: str = os.path.abspath(json_file)

    # Read JSON file
    try:
        with open(json_file, "r") as read_file:
            data: Dict = json.load(read_file)
            return data["PixelBandwidth"]
    except JSONDecodeError:
        pass 
        return'unknown'

def calc_read_time(file: str, 
                   json_file: Optional[str] = None
                   ) -> Tuple[float,float]:
    '''
    PENDING: newer versions of dcm2niix calcuate this value.

    Calculates the effective echo spacing and total readout time provided several combinations of parameters.
    Several approaches and methods to calculating the effective echo spacing and total readout within this function
    differ and are dependent on the parameters found within the provided JSON sidecar. Currently, there a four 
    approaches for calculating the effective echo space (all with differing values) and two ways of calculating 
    the total readout time. It should also be noted that several of these approaches are vendor specific (e.g. at 
    the time of writing, 16 Jan 2019, the necessary information for approach 1 is only found in Siemens DICOM 
    headers - the necessary information for approach 2 is only possible if the data is stored in PAR REC format as the
    WaterFatShift is a private tag in the Philips DICOM header - approaches 3 and 4 are intended for Philips/GE DICOMs 
    as those values are anticipated to exist in their DICOM headers).
    
    The approaches are listed below:
    
    Approach 1 (BIDS method, Siemens):
        BWPPPE = BandwidthPerPixelPhaseEncode
        EffectiveEchoSpacing = 1/[BWPPPE * ReconMatrixPE]
        TotalReadoutTime = EffectiveEchoSpacing * (ReconMatrixPE - 1)
        
    Approach 2 (Philips method - PAR REC):
        EffectiveEchoSpacing = (((1000 * WaterFatShift)/(434.215 * (EchoTrainLength + 1)))/ParallelReductionFactorInPlane)
        TotalReadoutTime = 0.001 * EffectiveEchoSpacing * EchoTrainLength
    
    Approach 3 (Philips/GE method - DICOM):
        EffectiveEchoSpacing = ((1/(PixelBandwidth * EchoTrainLength)) * (EchoTrainLength - 1)) * 1.3
        TotalReadoutTime = EffectiveEchoSpacing * (EchoTrainLength - 1)
        
    Approach 4 (Philips/GE method - DICOM):
        EffectiveEchoSpacing = ((1/(PixelBandwidth * ReconMatrixPE)) * (ReconMatrixPE - 1)) * 1.3
        tot_read_time = EffectiveEchoSpacing * (ReconMatrixPE - 1)
        
        Note: EchoTrainLength is assumed to be equal to ReconMatrixPE for approaches 3 and 4, as these values are generally close.
        Note: Approaches 3 and 4 appear to have about a 30% decrease in Siemens data when this was tested. The solution was to implement a fudge factor that accounted for the 30% decrease.
    
    Arguments:
        file (string): Absolute filepath to raw image data file (DICOM or PAR REC)
        json_file (string, optional): Absolute filepath to JSON sidecare
        
    Returns:
        eff_echo_sp (float): Effective Echo Spacing
        tot_read_time (float): Total Readout Time
        
    References:
    Approach 1: https://github.com/bids-standard/bids-specification/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md
    Approach 2: https://osf.io/hks7x/ - page 7; 
    https://support.brainvoyager.com/brainvoyager/functional-analysis-preparation/29-pre-processing/78-epi-distortion-correction-echo-spacing-and-bandwidth
    
    Forum that raised this specific issue with Philips: https://neurostars.org/t/consolidating-epi-echo-spacing-and-readout-time-for-philips-scanner/4406
    
    Approaches 3 and 4 were found thorugh trial and error and yielded similar, but not the same values as approaches 1 and 2.
    '''
    
    # check file extension
    if 'dcm' in file:
        calc_method = 'dcm'
    elif 'PAR' in file:
        calc_method = 'par'
        
    # Create empty string variables
    bwpppe = ''
    recon_mat = ''
    pix_band = ''
    wfs = ''
    etl = ''
    red_fact = ''
        
    if calc_method.lower() == 'dcm':
        bwpppe = cdm.get_bwpppe(file)
        if json_file:
            recon_mat = get_recon_mat(json_file)
            pix_band = get_pix_band(json_file)
            # set bandwidth per pixel to empty if unknown
            try:
                if bwpppe.lower() == 'unknown':
                    bwpppe = ''
            except AttributeError:
                pass
            # set pixel bandwidth to empty if unknown
            try:
                if pix_band.lower() == 'unknown':
                    pix_band = ''
            except AttributeError:
                pass
            etl = recon_mat
    elif calc_method.lower() == 'par':
        wfs = csp.get_wfs(file)
        etl = csp.get_etl(file)
        red_fact = csp.get_red_fact(file)
        # set water fat shift to empty if unknown
        try:
            if wfs.lower() == 'unknown':
                wfs = ''
        except AttributeError:
            pass
        # set echo train length to empty if unknown
        try:
            if etl.lower() == 'unknown':
                etl = ''
        except AttributeError:
            pass
         # set parallel reduction factor to empty if unknown
        try:
            if red_fact.lower() == 'unknown':
                red_fact = ''
        except AttributeError:
            pass
    
    # Calculate effective echo spacing and total readout time
    if bwpppe and recon_mat:
        eff_echo_sp = 1/(bwpppe * recon_mat)
        tot_read_time = eff_echo_sp * (recon_mat - 1)
    elif wfs and etl:
        if not red_fact:
            red_fact = 1
        eff_echo_sp = (((1000 * wfs)/(434.215 * (etl + 1)))/red_fact)
        tot_read_time = 0.001 * eff_echo_sp * etl
    elif pix_band and etl:
        eff_echo_sp = ((1/(pix_band * etl)) * (etl - 1)) * 1.3
        tot_read_time = eff_echo_sp * (etl - 1)
    elif pix_band and recon_mat:
        eff_echo_sp = ((1/(pix_band * recon_mat)) * (recon_mat - 1)) * 1.3
        tot_read_time = eff_echo_sp * (recon_mat - 1)
    else:
        eff_echo_sp = "unknown"
        tot_read_time = "unknown"
        
    return eff_echo_sp,tot_read_time

def convert_anat(file,work_dir,work_name):
    '''
    Converts raw anatomical (and functional) MR images to NifTi file format, with a BIDS JSON sidecar.
    Returns a NifTi file and a JSON sidecar (file) by globbing an isolated directory.
    
    Arguments:
        file (string): Absolute filepath to raw image data
        work_dir (string): Working directory
        work_name (string): Output file name
        
    Returns:
        nii_file (string): Absolute file path to NifTi image
        json_file (string): Absolute file path to JSON sidecar
    '''
    
    # Convert (anatomical) iamge data
    convert_image_data(file, work_name, work_dir)
    
    # Get files
    dir_path = os.path.join(work_dir, work_name)
    nii_file = glob.glob(dir_path + '*.nii*')
    json_file = glob.glob(dir_path + '*.json')
    
    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)
    
    return nii_file, json_file

def convert_dwi(file,work_dir,work_name):
    '''
    Converts raw diffusion weigthed MR images to NifTi file format, with a BIDS JSON sidecar.
    Returns a NifTi file, JSON sidecar (file), and (FSL-style) bval and bvec files by globbing 
    an isolated directory.
    
    Arguments:
        file (string): Absolute filepath to raw image data
        work_dir (string): Working directory
        work_name (string): Output file name
        
    Returns:
        nii_file (string): Absolute file path to NifTi image
        json_file (string): Absolute file path to JSON sidecar
        bval (string): Absolute file path to bval file
        bvec (string): Absolute file path to bvec file
    '''
    
    # Convert diffusion iamge data
    convert_image_data(file, work_name, work_dir)
    
    # Get files
    dir_path = os.path.join(work_dir, work_name)
    nii_file = glob.glob(dir_path + '*.nii*')
    json_file = glob.glob(dir_path + '*.json')
    bval = glob.glob(dir_path + '*.bval*')
    bvec = glob.glob(dir_path + '*.bvec*')
    
    # Convert lists to strings
    nii_file = ''.join(nii_file)
    json_file = ''.join(json_file)
    bval = ''.join(bval)
    bvec = ''.join(bvec)
    
    return nii_file, json_file, bval, bvec

def convert_fmap(file,work_dir,work_name):
    '''
    Converts raw precomputed fieldmap MR images to NifTi file format, with a BIDS JSON sidecar.
    Returns two NifTi files, and their corresponding JSON sidecars (files), by globbing an isolated directory.
    
    N.B.: This function is mainly designed to handle fieldmap data case 3 from bids-specifications document. Furhter support for 
    the additional cases requires test/validation data. 
    BIDS-specifications document located here: 
    https://github.com/bids-standard/bids-specification/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md
    
    Arguments:
        file (string): Absolute filepath to raw image data
        work_dir (string): Working directory
        work_name (string): Output file name
        
    Returns:
        nii_fmap (string): Absolute file path to NifTi image fieldmap
        json_fmap (string): Absolute file path to corresponding JSON sidecar
        nii_mag (string): Absolute file path to NifTi magnitude image
        json_mag (string): Absolute file path to corresponding JSON sidecar
    '''
    
    # Convert diffusion iamge data
    convert_image_data(file, work_name, work_dir)
    
    # Get files
    dir_path = os.path.join(work_dir, work_name)
    nii_fmap = glob.glob(dir_path + '*real*.nii*')
    json_fmap = glob.glob(dir_path + '*real*.json')
    nii_mag = glob.glob(dir_path + '.nii*')
    json_mag = glob.glob(dir_path + '.json')
    
    # Convert lists to strings
    nii_fmap = ''.join(nii_fmap)
    json_fmap = ''.join(json_fmap)
    nii_mag = ''.join(nii_mag)
    json_mag = ''.join(json_mag)

    return nii_fmap, json_fmap, nii_mag, json_mag
