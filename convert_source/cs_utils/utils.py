# -*- coding: utf-8 -*-
"""File utility functions for convert_source, which encapsulate file reading/writing for JSON files,
in addition to subject and session information data collection methods.
"""
import os
import glob
import gzip
import json
import platform
import re
import pydicom
import numpy as np

from collections import deque
from json import JSONDecodeError
from copy import deepcopy
from shutil import copy
from tqdm import tqdm

from typing import (
    List, 
    Dict, 
    Optional, 
    Set, 
    Tuple,
    Union
)

from convert_source.cs_utils.img_dir import img_dir_list

from convert_source.cs_utils.fileio import ( 
    Command,
    ConversionError, 
    TmpDir, 
    LogFile, 
    File, 
    NiiFile
)

from convert_source.imgio.dcmio import get_bwpppe

from convert_source.imgio.pario import(
    get_etl,
    get_red_fact,
    get_wfs
)

from convert_source.cs_utils.database import (
    construct_db_dict,
    insert_row_db,
    query_db
)

# Define exceptions
class SubInfoError(Exception):
    pass

# Define class(es)
class SubDataInfo():
    """Class instance that creates a data object that organizes a subject's 
    identification (ID) number, session ID number, the path to the image data 
    directory, and the unique file ID. This information is then stored for 
    each separate class instance, and can be accessed as shown in the example
    usage.

    Attributes:
        sub: Subject ID.
        data: Path to image data directory.
        ses: Session ID.
        file_id: Unique file ID for the source image data.
    
    Usage example:
        >>> sub_info = SubDataInfo(sub="002",
        ...                        data="<path/to/img/data>",
        ...                        ses="001",
        ...                        file_id="0000001")
        ...
        >>> sub_info.sub
        "002"
        >>> 
        >>> sub_info.ses
        "001"
        >>> sub_info.file_id
        "0000001"
    
    Arguments:
        sub: Subject ID.
        data: Path to image data directory.
        ses: Session ID.
        file_id: Unique file ID for the source image data.
    
    Raises:
        SubInfoError: Error that arises from either not specifying the subject ID or the path to the image file.
    """

    def __init__(self,
                 sub: Union[str,int],
                 data: str,
                 ses: Optional[Union[str,int]] = None,
                 file_id: Optional[Union[str,int]] = None):
        """Init doc-string for the 'SubDataInfo' class. 
        
        Arguments:
            sub: Subject ID.
            data: Path to image data directory.
            ses: Session ID.
            file_id: Unique file ID for the source image data.
        
        Raises:
            SubInfoError: Error that arises from either not specifying the subject ID or the path to the image file.
        """
        if sub:
            self.sub: str = str(sub)
        else:
            raise SubInfoError("Subject ID was not specified")

        if data:
            self.data: str = data
        else:
            raise SubInfoError("Subject data was not specified.")

        if ses:
            self.ses: str = str(ses)
        else:
            self.ses: str = ""
        
        if file_id:
            self.file_id: str = str(file_id)
        else:
            self.file_id: str = ""
    
    def __repr__(self):
        """NOTE: Returns string represented as dictionary."""
        return (str({"sub": self.sub,
                     "ses": self.ses,
                     "data": self.data,
                     "file_id": self.file_id}))

class BIDSimg():
    """File collection and organization object intended for handling 
    Brain Imaging Data Structure (BIDS) data in the process of being converted from source data to 
    NIFTI.
    
    Attributes:
        imgs: List of NIFTI files.
        jsons: Corresponding list of JSON sidecar(s).
        bvals: Corresponding list of bval file(s).
        bvecs: Corresponding list of bvec file(s).
    
    Arguments:
        work_dir: Input working directory that contains the image files and their associated output files.
    """

    def __init__(self,
                 work_dir: str):
        """Constructs class instance lists for NIFTI, JSON, bval, and bvec files.
        
        Arguments:
            work_dir: Input working directory that contains the image files and their associated output files.
        """
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
        """NOTE: Returns a string represented as a dictionary of list items."""
        return ( str({"imgs": self.imgs,
                      "jsons": self.jsons,
                      "bvals": self.bvals,
                      "bvecs": self.bvecs}) )
    
    def copy_img_data(self,
                      target_dir: str
                     ) -> Tuple[List[str],List[str],List[str],List[str]]:
        """Copies image data and their associated files to some target directory.

        NOTE: 
            This function resets the class attributes of the class instance with the returns of this function.
        
        Arguments:
            target_dir: Target directory to copy files to.
            
        Returns:
            Tuple of four lists:
                * NIFTI image files
                * Corresponding JSON file(s)
                * Corresponding bval file(s)
                * Corresponding bvec file(s)
        """
        
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

# Define function(s)

# def file_to_screen(file: str) -> str:
#     """Reads the contents of a file and prints it to screen.
# 
#     Arguments:
#         file: Path to file.
# 
#     Returns:
#         File contents returned as string, can be printed to screen.
#     """
# 
#     with open(file,"r") as f:
#         file_contents: str = f.read()
#         file_contents: str = file_contents.strip("\n")
#         f.close()
#     return file_contents

def zeropad(num: Union[str,int],
            num_zeros: int = 2
            ) -> str:
    """Zeropads a number, should that number be an int or str.
    
    Usage example:
        >>> zeropad(5,2)
        '05'
        >>> zeropad('5',2)
        '05'

    Arguments:
        num: Input number (as str or int) to zeropad.
        num_zeros: Number of zeroes to pad with.

    Returns:
        Zeropadded string of the number, or the original string if the input string could not be represented as an integer.

    Raises:
        TypeError: Error that arises if floats are passed as an argument.
    """
    if type(num) is float:
        raise TypeError("Only integers and strings can be used with the zeropad function.")
    try:
        num: str = str(num)
        num: str = num.zfill(num_zeros)
        return num
    except ValueError:
        return num

def add_to_zeropadded(num1: Union[int,str],
                      num2: int
                      ) -> str:
    """Adds some specified integer to another zeropadded integer.

    Usage example:
        >>> add_to_zeropadded('005',2)
        '007'
        
    Arguments:
        num1: Input integer, or zeropadded integer represented as a string.
        num2: Integer to add to ``num1``.

    Returns:
        Sum of the two perceived integer values, represented as a string.

    Raises:
        ValueError: Error that arises if non-integer string representations are passed as an argument for ``num1``.
        TypeError: Error that arise if non-integer arguments are passed for ``num2``, **OR** if floats are passed for either ``num1`` or ``num2``.
    """
    try:
        int(num1)
    except ValueError:
        raise ValueError(f"Input value {num1} is not an integer represented as a string.")

    if isinstance(num2,int) and (isinstance(num1,int) or isinstance(num1,str)):
        if isinstance(num1,int):
            pad_len: int = 0
        else:
            pad_len: int = len(num1)
        new_num: int = int(num1) + num2
        return zeropad(num=new_num,num_zeros=pad_len)
    else:
        raise TypeError(f"Input {num1} is not a string or integer OR {num2} is not an integer. Please check.")

def get_echo(json_file: str) -> float:
    """Reads the echo time (TE) from the NIFTI JSON sidecar and returns it.

    Arguments:
        json_file (string): Absolute path to JSON sidecar.

    Returns:
        Echo time as a float.
    """

    # Get absolute path to file
    json_file: str = os.path.abspath(json_file)

    with open(json_file, "r") as read_file:
        data = json.load(read_file)
    echo = data.get("EchoTime")
    return float(echo)

def gzip_file(file: str,
              cprss_lvl: int = 6,
              native: bool = True
              ) -> str:
    """Gzips file. Native implementation of gzipping files is prefered with
    this function provided that the system is UNIX. Otherwise, a pythonic 
    implementation of gzipping is performed.
    
    Arguments:
        file: Input file.
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest.
        native: Uses native implementation of gzip.
        
    Returns: 
        Gzipped file.
    """

    # Check if native method was enabled.
    if native:
        if platform.system().lower() == 'windows':
            native = False
        else:
            native = True
    
    if native:
        # Native implementation
        tmp_file: str = file
        tmp_file: File = File(tmp_file)
        [path, filename, ext] = tmp_file.file_parts()
        out_file: str = os.path.join(path,filename + ext + '.gz')
        gzip_cmd: Command = Command("gzip")
        gzip_cmd.cmd_list.append(f"-{cprss_lvl}")
        gzip_cmd.cmd_list.append(file)
        gzip_cmd.run()
        return out_file
    else:
        # Define tempory file for I/O buffer stream
        tmp_file: File = File(file)
        [path, filename, ext] = tmp_file.file_parts()
        out_file: str = os.path.join(path,filename + ext + '.gz')
        
        # Pythonic gzip
        with open(file,"rb") as in_file:
            data = in_file.read(); in_file.close()
            with gzip.GzipFile(out_file,"wb",compresslevel=cprss_lvl) as tmp_out:
                tmp_out.write(data)
                tmp_out.close()
                os.remove(file) 
        return out_file

def gunzip_file(file: str,
                native: bool = True
                ) -> str:
    """Gunzips file. Native implementation of gunzipping files is prefered with
    this function provided that the system is UNIX. Otherwise, a pythonic 
    implementation of gunzipping is performed.
    
    Arguments:
        file: Input file.
        native: Uses native implementation of gunzip.
        
    Returns: 
        Gunzipped file.
    """

    # Check if native method was enabled.
    if native:
        if platform.system().lower() == 'windows':
            native = False
        else:
            native = True
    
    if native:
        # Native implementation
        tmp_file: str = file
        tmp_file: File = File(tmp_file)
        [path, filename, ext] = tmp_file.file_parts()
        out_file: str = os.path.join(path,filename + ext[:-3])
        gunzip_cmd: Command = Command("gunzip")
        gunzip_cmd.cmd_list.append(file)
        gunzip_cmd.run()
        return out_file
    else:
        # Define tempory file for I/O buffer stream
        tmp_file: File = File(file)
        [path, filename, ext] = tmp_file.file_parts()
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
    """Reads JavaScript Object Notation (JSON) file.
    
    Arguments:
        json_file: Input file.
        
    Returns: 
        Dictionary of key mapped items from JSON file.
    """

    # Get absolute path to file
    if ('.json' in json_file) and os.path.exists(json_file):
        pass
    else:
        json_file: str = ""
    
    # Read JSON file
    if json_file:
        json_file: str = os.path.abspath(json_file)
        with open(json_file) as file:
            return json.load(file)
    else:
        return dict()

def write_json(json_file: str,
               dictionary: Dict
               ) -> str:
    """Writes python dictionary to a JavaScript Object Notation (JSON) file. The speicifed JSON file need not exist.
    
    Usage example:
        >>> json_file = write_json("file.json",
        ...                        example_dict)
        ...

    Arguments:
        json_file: Input JSON file.
        dictionary: Input python dictionary

    Returns:
        String that represents path to written JSON file.
    """

    # Check if JSON file exists, if not, then create JSON file
    if not os.path.exists(json_file):
        with open(json_file,"w"): pass
    
    # Get absolute path to file
    json_file: str = os.path.abspath(json_file)
    
    # Write updated JSON file
    with open(json_file,"w") as file:
        json.dump(dictionary,file,indent=4)

    return json_file

def update_json(json_file: str,
                dictionary: Dict
                ) -> str:
    """Updates JavaScript Object Notation (JSON) file. If the file does not exist, it is created once
    this function is called.
    
    Arguments:
        json_file: Input file.
        dictionary: Dictionary of key mapped items to write to JSON file.
        
    Returns: 
        Updated JSON file.
    """
    
    # Check if JSON file exists, if not, then create JSON file
    if not os.path.exists(json_file):
        with open(json_file,"w"): pass
    
    # Get absolute path to file
    json_file: str = os.path.abspath(json_file)

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
    """Updates a dictionary multiple times depending on the number key word mapped pairs that are provided and 
    returns a separate updated dictionary. The dictionary passed as an argument need not exist at runtime.
    
    Example usage:
        >>> new_dict = dict_multi_update(old_dict,
        ...                              Manufacturer="Philips",
        ...                              ManufacturersModelName="Ingenia",
        ...                              MagneticFieldStrength=3,
        ...                              InstitutionName="CCHMC")
        ... 
    
    Arguments:
        dictionary: Dictionary of key mapped items to be updated.
        **kwargs: Key-value (key=value) pairs.
        
    Returns: 
        New updated dictionary.
    """
    
    # Create new dictionary
    if dictionary:
        new_dict: Dict = deepcopy(dictionary)
    else:
        new_dict: Dict = {}
    
    for key,item in kwargs.items():
        tmp_dict: Dict = {key:item}
        new_dict.update(tmp_dict)
    return new_dict

def get_bvals(bval_file: Optional[str] = ""
              ) -> List[int]:
    """Reads the bvals from the (FSL-style) bvalue file and returns a list of unique non-zero bvalues.
    If the bval file does not exist or is not provided, then zero is returned in a list.
    
    Arguments:
        bval_file: Bval (.bval) file.
        
    Returns: 
        List of unique, non-zero bvalues (as ints), or zero in a list.
    """
    if bval_file and os.path.exists(bval_file):
        bval_file: str = os.path.abspath(bval_file)
        vals = np.loadtxt(bval_file)
        vals_int = [ int(i) for i in vals ]
        vals_nonzero = [ i for i in vals_int if i != 0 ]
        bvals: List[float] = list(np.unique(vals_nonzero))
        return [ int(i) for i in bvals ]
    else:
        return [0]

def get_metadata(dictionary: Optional[Dict] = None,
                 modality_type: Optional [str] = None,
                 task: Optional[str] = None
                 ) -> Tuple[Dict[str,str],Dict[str,Union[int,str]]]:
    """Reads the metadata dictionary and looks for keywords to indicate what metadata should be written to which
    dictionary. For example, the keyword 'common' is used to indicate the common information for the imaging
    protocol and may contain information such as: field strength, phase encoding direction, institution name, etc.
    Additional keywords that are BIDS sub-directories names (e.g. anat, func, dwi) will return an additional
    dictionary which contains metadata specific for those modalities. 'Func' also has additional keywords based on
    the task specified. If an empty dictionary is passed as an argument, then this function returns empty dictionaries
    as a result.
    
    Arguments:
        dictionary: Nested dictionary of key mapped items from the 'read_config' function.
        modality_type: BIDS modality type (e.g. anat, func, dwi, etc.).
        task: Task name to search in the key mapped dictionary.
        
    Returns:
        Tuple:
            * Common metadata dictionary.
            * Modality specific metadata dictionaries.
    """

    if dictionary:
        pass
    else:
        dictionary: Dict = {}
    
    # Create empty dictionaries
    com_param_dict: Dict = {}
    scan_param_dict: Dict = {}
    scan_task_dict: Dict = {}
    
    # Iterate through, looking for key words (e.g. common and modality_type)
    for key,item in dictionary.items():
        # BIDS common metadata fields (normally shared by all modalities)
        if key.lower() in 'common':
            com_param_dict = dictionary[key]

        # BIDS modality specific metadata fields
        if key.lower() in modality_type:
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
    """Searches a string using a list that contains substrings. Returns boolean 'True' or 'False' 
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
    """

    for word in in_list:
        if any(word.lower() in in_str.lower() for element in in_str.lower()):
            return True
    return False

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
                       crop_3D: str = 'n',
                       lossless: bool = False,
                       big_endian: str = "o",
                       xml: bool = False,
                       log: Optional[LogFile] = None,
                       env: Optional[Dict] = None,
                       dryrun: bool = False,
                       return_obj: bool = False
                       ) -> Union[BIDSimg,Tuple[List[str],List[str],List[str],List[str]]]:
    """Converts medical image data (``DICOM``, ``PAR REC``, or ``Bruker``) to ``NIFTI`` (or NRRD, not recommended) using ``dcm2niix``.
    This is a wrapper function for ``dcm2niix`` (v1.0.20201102+).

    NOTE: 
        **IF** ``dcm2niix`` is not in system path, then its parent's directory path can be appended to the system's ``PATH`` variable by doing:

            >>> from convert_source.cs_utils.fileio import Command
            >>> dcm2niix_command = Command("dcm2niix")
            >>> dcm2niix_command.check_dependency(path_envs=['<path/to/dcm2niix/dir>'])

        One should note that argument passed for the ``path_envs`` argument is a list.
        Additionally, the last statement above should return `True` if the executable is found, or raise 
        a ``DependencyError`` otherwise.

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
        dir_search: Directory search depth (default: 5).
        nrrd: Export as NRRD instead of NifTi, not recommended (default: False).
        ignore_2D: Ignore derived, localizer and 2D images (default: True).
        merge_2D: Merge 2D slices from same series regardless of echo, exposure, etc. (default: True).
        text: Text notes includes private patient details in separate text file (default: False).
        progress: Report progress, slicer format progress information (default: False).
        verbose: Enable verbosity (default: False).
        write_conflicts: Write behavior for name conflicts:

            * 'suffix' = Add suffix to name conflict (default)
            * 'overwrite' = Overwrite name conflict
            * 'skip' = Skip name conflict

        crop_3D: Crop 3D acquisitions (y/n/i, default n, use 'i'gnore to neither crop nor rotate 3D acquistions).
        lossless: Losslessly scale 16-bit integers to use dynamic range (default: True).
        big_endian: Byte order:

            * 'o' = optimal/native byte order (default)
            * 'n' = little endian
            * 'y' = big endian

        xml: Slicer format features (default: False).
        log: LogFile object for logging.
        env: Path environment dictionary.
        dryrun: Perform dryrun (creates the command, but does not execute it).
        return_obj: Boolean to return object, rather than a tuple of lists.
        
    Returns:
        BIDSimg data object or Tuple of lists

        BIDSimg data object:
            * imgs: List of NIFTI image files
            * jsons: Corresponding list of JSON file(s)
            * bvals: Corresponding bval file(s)
            * bvecs: Corresponding bvec file(s)

        **OR**

        Tuple:
            * List of NIFTI image files
            * List of corresponding JSON file(s)
            * List of corresponding bval file(s)
            * List of corresponding bvec file(s)
    
    Raises:
        ConversionError: Error that arises if no converted (NIFTI) images are created.
        IndexError: Error that arises if the specified options arrays/lists are of different lengths.
    """
    
    # Get OS platform and construct command line args
    if platform.system().lower() == 'windows':
        convert: Command = Command("dcm2niix.exe")
    else:
        convert: Command = Command("dcm2niix")

    # Boolean True/False options arrays
    # 
    # IMPROVEMENT: 
    #   This could be re-done using a dictionary/hash map for better readability.
    bool_opts: List[Union[str,bool]] = [bids, anon_bids, gzip, comment, adjacent, nrrd, ignore_2D, merge_2D, text, verbose, lossless]
    bool_vars: List[str] = ["-b", "-ba", "-z", "-c", "-a", "-e", "-i", "-m", "-t", "-v", "-l"]

    # Initial option(s)
    if cprss_lvl:
        convert.cmd_list.append(f"-{cprss_lvl}")
    
    if dir_search:
        convert.cmd_list.append("-d")
        convert.cmd_list.append(f"{dir_search}")
    
    if crop_3D:
        if (crop_3D.lower() == 'y') or (crop_3D.lower() == 'n') or (crop_3D.lower() == 'i'):
            convert.cmd_list.append("-x")
            convert.cmd_list.append(crop_3D)
        else:
            crop_3D = 'n'
            convert.cmd_list.append("-x")
            convert.cmd_list.append(crop_3D)

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
        convert.cmd_list.append("--big-endian")
        convert.cmd_list.append("o")
    elif big_endian.lower() == "n":
        convert.cmd_list.append("--big-endian")
        convert.cmd_list.append("n")
    elif big_endian.lower() == "y":
        convert.cmd_list.append("--big-endian")
        convert.cmd_list.append("y")
    
    # Boolean option(s)
    if progress:
        convert.cmd_list.append("--progress")
    
    if xml:
        convert.cmd_list.append("--xml")
    
    if len(bool_opts) == len(bool_vars):
        for opt in zip(bool_opts,bool_vars):
            if opt[0]:
                convert.cmd_list.append(opt[1])
                convert.cmd_list.append("y")
    else:
        raise IndexError("Comparing arrays of two different lengths.")

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
        
        # Execute command (assumes dcm2niix is added to system path variable)
        convert.run(log=log,env=env,dryrun=dryrun)
        
        # Copy files to output directory
        img_data = BIDSimg(work_dir=tmp_dir.tmp_dir)
        [imgs, jsons, bvals, bvecs] = img_data.copy_img_data(target_dir=out_dir)
        
        # Clean-up
        tmp_dir.rm_tmp_dir(rm_parent=False)
    
    # Image file check
    if len(imgs) == 0:
        raise ConversionError("Image conversion error. No output images were found.")

    if return_obj:
        return img_data
    else:
        return imgs, jsons, bvals, bvecs

def glob_dcm(dcm_dir: str) -> List[str]:
    """Globs subject DICOM data directories for the top-most DICOM file
    in each respective directory.
    
    Example usage:
        >>> dcm_files = glob_dcm(dcm_dir)
        
    Arguments:
        dcm_dir: Subject DICOM data directory.
        
    Returns:
        List of strings of image files.
    """
    dcm_dir: str = os.path.abspath(os.path.realpath(dcm_dir))
    dir_search: str = os.path.join(dcm_dir,"*")
    dcm_dir_list: List[str] = glob.glob(dir_search)
    
    dcm_files: List[str] = []
    
    for dir_ in dcm_dir_list:
        for root, dirs, files in os.walk(dir_):
            # Only need the first DICOM file
            tmp_dcm_file = files[0]
            tmp_dcm_dir = root
            tmp_file = os.path.join(tmp_dcm_dir, tmp_dcm_file)

            # Old implementation - need to test with current use cases
            dcm_files.append(tmp_file)
            break
            
            # if '.dcm' in tmp_file:
            #     dcm_files.append(tmp_file)
            #     break
    return dcm_files

def glob_img(img_dir: str) -> List[str]:
    """Globs image data files given a subject image data directory.
    The image file types that are search for are:

        * ``DICOM``
        * ``PAR REC``
        * ``NIFTI``
    
    Example usage:
        >>> img_list = glob_img(img_dir)
        
    Arguments:
        img_dir: Path to image directory.
        
    Returns:
        List of strings of file paths to images.
    """
    img_dir: str = os.path.abspath(os.path.realpath(img_dir))

    # Listed in most desirable order
    img_types: List[str] = [ "dcm", "PAR", "nii" ]
        
    img_list: List[str] = []
        
    for img_type in img_types:
                
        dir_search: str = os.path.join(img_dir,f"*.{img_type}*")
        tmp_list: List[str] = glob.glob(dir_search)
        img_list.extend(tmp_list)
        
        tmp_list: List[str] = glob_dcm(dcm_dir=img_dir)
        img_list.extend(tmp_list)
    return img_list

def img_exclude(img_list: List[str],
               exclusion_list: Optional[List[str]] = None
               ) -> List[str]:
    """Constructs a new list with files that DO NOT contain words in the exclusion list.
    Should this list be empty, then the original input list is returned.
    
    Usage example:
        >>> new_img_list = img_exclude(img_list, ["SWI", "PD","ProtonDensity"])
        
    Arguments:
        img_list: Input list of paths to image files.
        exclusion_list: Exclusion list that consists of keywords used to exclude files. 
        
    Returns:
        List of image files that do not contain words in the exclusion list.
    """
    if (exclusion_list is None) or (len(exclusion_list) == 0):
        img_set: Set = set(img_list)
        new_list: List[str] = list(img_set)
        new_list.sort(reverse=False)
        return new_list
    else:
        img_set: Set = set(img_list)
        exclusion_set: Set = set()
        tmp_list: List[str] = []

        for file in exclusion_list:
            for img in img_list:
                if file.lower() in img.lower():
                    tmp_list.append(img)
            exclusion_set.update(set(tmp_list))
        new_list: List[str] = list(img_set.difference(exclusion_set))
        new_list.sort(reverse=False)
        return new_list

def collect_info(parent_dir: str,
                database: str,
                exclusion_list: Optional[List[str]] = None,
                log: Optional[LogFile] = None
                ) -> List[SubDataInfo]:
    """Collects image data information for each subject for a study, 
    provided there exists some parent directory. Certain image files 
    can be excluded provided a list of exclusion keywords/terms.

    Usage example:
        >>> data = collect_info("<parent/directory>",
        ...                     "file.db",
        ...                     ["SWI", "PD", "ProtonDensity"])
        ...
        >>>
        >>> data[0].sub
        "001"
        >>> 
        >>> data[0].data
        "<path/to/data>"
        >>> 
        >>> data[0].ses
        "001"
        >>>
        >>> data[0].file_id
        "0000001"
    
    Arguments:
        parent_dir: Parent directory that contains each subject.
        database: Database filename.
        exclusion_list: Exclusion list that consists of keywords used to exclude files. 
        log: LogFile object for logging.
        
    Returns:
        List/Array of SubDataInfo objects that corresponds to a subject ID, session ID, path to medical image data, and unique file ID.
    """
    parent_dir: str = os.path.abspath(parent_dir)
    data: List[SubDataInfo] = []

    path_sep: str = os.path.sep
    
    # Get image directory information
    [dir_list, _] = img_dir_list(directory=parent_dir,
                                        verbose=False)

    # Iterate through each subject image directory
    for img_dir in tqdm(dir_list,
                        desc="Searching subject directories",
                        position=0,
                        leave=True):
        # Set empty variables
        sub: str = ""
        ses: str = ""
        img_list: List[str] = []
        tmp_list: List[str] = []
        
        # Get subject and session ID from file path
        try:
            [sub, ses] = img_dir.replace(parent_dir + path_sep,"").split(sep=path_sep)[0].split(sep="-")
        except ValueError:
            ses = ""
            sub = img_dir.replace(parent_dir + path_sep,"").split(sep=path_sep)[0]
        
        # Glob and grab individual files
        tmp_list: List[str] = glob_img(img_dir=img_dir)
        img_list.extend(tmp_list)
        
        # Exclude files
        img_list = img_exclude(img_list=img_list,
                               exclusion_list=exclusion_list)
        
        for img in img_list:
            db_info: Dict[str,str] = construct_db_dict(study_dir=parent_dir,
                                                        sub_id=sub,
                                                        ses_id=ses,
                                                        file_name=img,
                                                        database=database,
                                                        use_dcm_dir=True)
            file_id: str = query_db(database=database,
                                    table='rel_path',
                                    prim_key='rel_path',
                                    column='file_id',
                                    value=db_info.get('rel_path',''))
            if file_id:
                if log:
                    log.log("Imaging data has already been processed and is stored in the database.")
            else:
                database: str = insert_row_db(database=database,
                                                info=db_info)
                sub_info: SubDataInfo = SubDataInfo(sub=sub,
                                                    data=img,
                                                    ses=ses,
                                                    file_id=db_info.get('file_id',''))
                data.append(sub_info)
    return data

def get_recon_mat(json_file: str) -> Union[float,str]:
    """Reads ReconMatrixPE (reconstruction matrix phase encode) value from the JSON sidecar.
    
    Arguments:
        json_file: BIDS JSON file.
        
    Returns:
        Recon Matrix PE value (as a float if it exists in the file, or as an empty string if not in the file).
    """

    json_file: str = os.path.abspath(json_file)
    
    # Read JSON file
    try:
        with open(json_file, "r") as read_file:
            data: Dict = json.load(read_file)
            return data.get("ReconMatrixPE","")
    except JSONDecodeError:
        return ''

def get_pix_band(json_file: str) -> Union[float,str]:
    """Reads pixel bandwidth value from the JSON sidecar.
    
    Arguments:
        json_file (string): BIDS JSON file.
        
    Returns:
        Pixel bandwidth value (as a float if it exists in the file, or as an empty string if not in the file).
    """
    
    json_file: str = os.path.abspath(json_file)

    # Read JSON file
    try:
        with open(json_file, "r") as read_file:
            data: Dict = json.load(read_file)
            return data.get("PixelBandwidth","")
    except JSONDecodeError:
        return''

def calc_read_time(file: str, 
                   json_file: Optional[str] = ""
                   ) -> Union[Tuple[float,float],Tuple[str,str]]:
    """Calculates the effective echo spacing and total readout time provided several combinations of parameters.
    Several approaches and methods to calculating the effective echo spacing and total readout within this function
    differ and are dependent on the parameters found within the provided JSON sidecar. Currently, there a four 
    approaches for calculating the effective echo space (all with differing values) and two ways of calculating 
    the total readout time. It should also be noted that several of these approaches are vendor specific (e.g. at 
    the time of writing, 16 Jan 2019, the necessary information for approach 1 is only found in Siemens DICOM 
    headers - the necessary information for approach 2 is only possible if the data is stored in PAR REC format as the
    WaterFatShift is a private tag in the Philips DICOM header - approaches 3 and 4 are intended for Philips/GE DICOMs 
    as those values are anticipated to exist in their DICOM headers).

    NOTE: 
        This function's calculation of the Effective Echo Spacing and the Total Readout Time ASSUME that the magnetic field strength is 3T.
    
    The approaches are listed below:
    
    Approach 1 (BIDS method, Siemens):
        ``BWPPPE = BandwidthPerPixelPhaseEncode``
        ``EffectiveEchoSpacing = 1/[BWPPPE * ReconMatrixPE]``
        ``TotalReadoutTime = EffectiveEchoSpacing * (ReconMatrixPE - 1)``
        
    Approach 2 (Philips method - PAR REC):
        ``EffectiveEchoSpacing = (((1000 * WaterFatShift)/(434.215 * (EchoTrainLength + 1)))/ParallelReductionFactorInPlane)``
        ``TotalReadoutTime = 0.001 * EffectiveEchoSpacing * EchoTrainLength``
    
    Approach 3 (Philips/GE method - DICOM):
        ``EffectiveEchoSpacing = ((1/(PixelBandwidth * EchoTrainLength)) * (EchoTrainLength - 1)) * 1.3``
        ``TotalReadoutTime = EffectiveEchoSpacing * (EchoTrainLength - 1)``
        
    Approach 4 (Philips/GE method - DICOM):
        ``EffectiveEchoSpacing = ((1/(PixelBandwidth * ReconMatrixPE)) * (ReconMatrixPE - 1)) * 1.3``
        ``tot_read_time = EffectiveEchoSpacing * (ReconMatrixPE - 1)``
        
    NOTE: 
        EchoTrainLength is assumed to be equal to ReconMatrixPE for approaches 3 and 4, as these values are generally close.
    NOTE: 
        Approaches 3 and 4 appear to have about a 30% decrease in Siemens data when this was tested. The solution was to implement a fudge factor that accounted for the 30% decrease.
    
    References:
        * Approach 1: 
            https://github.com/bids-standard/bids-specification/blob/master/src/04-modality-specific-files/01-magnetic-resonance-imaging-data.md
        * Approach 2: 
            https://osf.io/hks7x/ - page 7; 
            https://support.brainvoyager.com/brainvoyager/functional-analysis-preparation/29-pre-processing/78-epi-distortion-correction-echo-spacing-and-bandwidth
    
        * Forum that raised this specific issue with Philips MR data: 
            https://neurostars.org/t/consolidating-epi-echo-spacing-and-readout-time-for-philips-scanner/4406
    
        * Approaches 3 and 4:
            Found thorugh trial and error and yielded similar, but not the same values as approaches 1 and 2.
    
    Arguments:
        file: Filepath to raw image data file (DICOM or PAR REC)
        json_file: Filepath to corresponding JSON sidecar.
        
    Returns:
        Tuple:
            Tuple of floats or empty strings if unable to determine either of the values.
    """
    file: str = os.path.abspath(file)

    if json_file:
        json_file: str = os.path.abspath(json_file)

    # check file extension
    if '.dcm' in file:
        calc_method = 'dcm'
    elif '.PAR' in file:
        calc_method = 'par'
        
    # Create empty string variables
    bwpppe = ''
    recon_mat = ''
    pix_band = ''
    wfs = ''
    etl = ''
    red_fact = ''
        
    if calc_method.lower() == 'dcm':
        bwpppe = get_bwpppe(file)
        if json_file:
            recon_mat = get_recon_mat(json_file)
            pix_band = get_pix_band(json_file)
            etl = recon_mat
    elif calc_method.lower() == 'par':
        wfs = get_wfs(file)
        etl = get_etl(file)
        red_fact = get_red_fact(file)
    
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
        eff_echo_sp = ""
        tot_read_time = ""
        
    return eff_echo_sp,tot_read_time

def comp_dict(d1: Dict, 
              d2: Dict, 
              path: Optional[str] = "", 
              verbose: bool = False
             ) -> Union[bool,None]:
    """Compares 2 dictionaries to see if they have matching keys, and that each key maps
    to a value (that is **NOT** of type None). This is performed recursively.
    
    Usage example:
        >>> comp_dict(d1, d2)
        True
        
    Arguments:
        d1: Input dictionary.
        d2: Input dictionary.
        path: Visualized path that has been traversed.
        verbose: Print verbose output.
        
    Returns:
        Boolean 'True', raises exceptions otherwise.
        
    Raises:
        KeyError: Error that arises if input dictionaries do not have matching keys.
        ValueError: Error that arises if one or more of the keys in either dictionary map NoneType values.
    """
    for k in d1:
        if (k not in d2):
            if verbose:
                print (path, ":")
                print (k + " as key not in d2", "\n")
            raise KeyError("Input dictionaries do not have matching keys")
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    if verbose:
                        path = path + "->" + k
                    pass
                comp_dict(d1[k],d2[k], path, verbose)
            else:
                if d1[k] != d2[k] and (d1[k] is None or d2[k] is None):
                    if verbose:
                        print (path, ":")
                        print (" - ", k," : ", d1[k])
                        print (" + ", k," : ", d2[k])
                    raise ValueError("One or both input BIDS dictionaries map to NoneType values.")
    return True

def depth(d: Dict) -> int:
    """Uses breadth-first search approach to find the depth of a dictionary.
    
    Usage example:
        >>> depth(d)
        3
    
    Arguments:
        d: Input dictionary.
        
    Returns:
        Number of levels in dictionary.
    """
    queue = deque([(id(d), d, 1)])
    memo = set()
    while queue:
        id_, o, level = queue.popleft()
        if id_ in memo:
            continue
        memo.add(id_)
        if isinstance(o, dict):
            queue += ((id(v), v, level + 1) for v in o.values())
    return level

def list_dict(d: Dict[str,str]
             ) -> List[Dict[str,str]]:
    """Creates a list of dictionaries provided a nested dictionary using the
    top-most level of the dictionaries as list (array) indices. 
    
    Usage example:
        >>> list_dict(d)
        [d1, d2, ..., dn]
    
    Arguments:
        d: Input (nested) dictionary.
        
    Returns:
        List of dictionaries.
    """
    arr: List = []
    for k,v in d.items():
        tmp: Dict = {k:v}
        arr.append(tmp)
    return arr

def get_par_scan_tech(par_file: str,
                      search_dict: Dict
                      ) -> Tuple[str,str,str]:
    """Searches PAR file header for scan technique/MR modality used in accordance with the search terms provided by the
    nested heursitic search dictionary. A regular expression (regEx) search string is defined and is searched in the 
    PAR header file.
    
    Usage example:
        >>> [modality_type, modality_label, task] = get_par_scan_tech(par_file,
        ...                                                           search_dict)
        ...

    Arguments:
        par_file: PAR header filename.
        search_dict: Nested heursitic search dictionary (from the ``read_config`` function).
    
    Returns: 
        Tuple:
            * ``modality_type``: Modality type (e.g. ``anat``, ``func``, etc.)
            * ``modality_label``: Modality label (e.g. ``T1w``, ``bold``, etc.)
            * ``task``: Task name (e.g. ``rest``).
    """
    par_file: str = os.path.abspath(par_file)

    search_arr: List[str] = list_dict(d=search_dict)

    mod_found: bool = False

    # Define regEx search string
    regexp: re = re.compile(r'.    Technique                          :  .*', re.M | re.I)
    
    # Open and search PAR header file
    with open(par_file) as f:
        for line in f:
            match_ = regexp.match(line)
            if match_:
                par_scan_tech_str: str = match_.group()

    if par_scan_tech_str:
        pass
    else:
        return "","",""
    
    # Set returns to empty strings
    modality_type: str = ""
    modality_label: str = ""
    task: str = ""

    # Use matching string in search dictionary
    for i in search_arr:
        if mod_found:
            break
        for k,v in i.items():
            if depth(i) == 3:
                for k2,v2 in v.items():
                    mod_type: str = k
                    mod_label: str = k2
                    mod_task: str = ""
                    mod_search: List[str] = v2
                    if list_in_substr(in_list=mod_search,in_str=par_scan_tech_str):
                        mod_found: bool = True
                        modality_type: str = mod_type
                        modality_label: str = mod_label
                        task: str = mod_task
            elif depth(i) == 4:
                for k2,v2 in v.items():
                    for k3,v3 in v2.items():
                        mod_type: str = k
                        mod_label: str = k2
                        mod_task: str = k3
                        mod_search: List[str] = v3
                        if list_in_substr(in_list=mod_search,in_str=par_scan_tech_str):
                            mod_found: bool = True
                            modality_type: str = mod_type
                            modality_label: str = mod_label
                            task: str = mod_task

    return (modality_type, 
            modality_label, 
            task)

def get_dcm_scan_tech(dcm_file: str,
                      search_dict: Dict
                      ) -> Tuple[str,str,str]:
    """Searches DICOM file header for scan technique/MR modality used in accordance with the search terms provided by the
    nested heursitic search dictionary. The DICOM header field searched is a Philips DICOM private tag (2001,1020) [Scanning 
    Technique Description MR]. In the case that matches are found in that field, is empty, or does not exist - then common 
    DICOM tags are searched which include: 

        * Series Description
        * Protocol Name
        * Image Type.
    
    Usage example:
        >>> [modality_type, modality_label, task] = get_dcm_scan_tech(dcm_file,
        ...                                                           search_dict)
        ...
    
    Arguments:
        dcm_file: DICOM filename.
        search_dict: Nested heursitic search dictionary (from the ``read_config`` function).
    
    Returns: 
        Tuple:
            * ``modality_type``: Modality type (e.g. ``anat``, ``func``, etc.)
            * ``modality_label``: Modality label (e.g. ``T1w``, ``bold``, etc.)
            * ``task``: Task name (e.g. ``rest``).
    """
    dcm_file: str = os.path.abspath(dcm_file)

    search_arr: List[str] = list_dict(d=search_dict)

    mod_found: bool = False

    # Set returns to empty strings
    modality_type: str = ""
    modality_label: str = ""
    task: str = ""

    ds = pydicom.dcmread(dcm_file)

    # Search DICOM header for Scan Technique
    dcm_scan_tech_str = str(ds[0x2001,0x1020])

    # Use dictionary to search in string
    for i in search_arr:
        if mod_found:
            break
        for k,v in i.items():
            if depth(i) == 3:
                for k2,v2 in v.items():
                    mod_type: str = k
                    mod_label: str = k2
                    mod_task: str = ""
                    mod_search: List[str] = v2
                    if list_in_substr(in_list=mod_search,in_str=dcm_scan_tech_str):
                        mod_found: bool = True
                        modality_type: str = mod_type
                        modality_label: str = mod_label
                        task: str = mod_task
            elif depth(i) == 4:
                for k2,v2 in v.items():
                    for k3,v3 in v2.items():
                        mod_type: str = k
                        mod_label: str = k2
                        mod_task: str = k3
                        mod_search: List[str] = v3
                        if list_in_substr(in_list=mod_search,in_str=dcm_scan_tech_str):
                            mod_found: bool = True
                            modality_type: str = mod_type
                            modality_label: str = mod_label
                            task: str = mod_task

    if mod_found:
        return (modality_type, 
                modality_label, 
                task)

    # Secondary searches in the case that the Private Tag/Field (2001, 1020) [Scanning Technique Description MR] search is unsucessful

    # Define list of DICOM header fields to search
    dcm_fields: List[str] = ['SeriesDescription', 'ImageType', 'ProtocolName']

    for dcm_field in dcm_fields:
            dcm_scan_tech_str = str(eval(f"ds.{dcm_field}")) # This makes me dangerously uncomfortable

            # Use dictionary to search in string
            for i in search_arr:
                if mod_found:
                    break
                for k,v in i.items():
                    if depth(i) == 3:
                        for k2,v2 in v.items():
                            mod_type: str = k
                            mod_label: str = k2
                            mod_task: str = ""
                            mod_search: List[str] = v2
                            if list_in_substr(in_list=mod_search,in_str=dcm_scan_tech_str):
                                mod_found: bool = True
                                modality_type: str = mod_type
                                modality_label: str = mod_label
                                task: str = mod_task
                    elif depth(i) == 4:
                        for k2,v2 in v.items():
                            for k3,v3 in v2.items():
                                mod_type: str = k
                                mod_label: str = k2
                                mod_task: str = k3
                                mod_search: List[str] = v3
                                if list_in_substr(in_list=mod_search,in_str=dcm_scan_tech_str):
                                    mod_found: bool = True
                                    modality_type: str = mod_type
                                    modality_label: str = mod_label
                                    task: str = mod_task

    return (modality_type, 
            modality_label, 
            task)

def header_search(img_file: str, 
                  search_dict: Dict
                  ) -> Tuple[str,str,str]:
    """Searches a DICOM or PAR file header for relevant scan technique/parameter information provided a nested heursitic search dictionary
    of search terms to map scan acquisitions of interest. Any other image file passed as an argument will return a tuple of empty strings.

    Usage example:
        >>> [modality_type, modality_label, task] = header_search(img_file,
        ...                                                       search_dict)
        ...

    Arguments:
        img_file: Image file.
        search_dict: Nested heursitic search dictionary (from the ``read_config`` function).
    
    Returns: 
        Tuple:
            * ``modality_type``: Modality type (e.g. ``anat``, ``func``, etc.)
            * ``modality_label``: Modality label (e.g. ``T1w``, ``bold``, etc.)
            * ``task``: Task name (e.g. ``rest``).
    """
    img_file: str = os.path.abspath(img_file)

    if '.dcm' in img_file.lower():
        [ modality_type, modality_label, task ] = get_dcm_scan_tech(dcm_file=img_file,
                                                                    search_dict=search_dict)  
    elif '.par' in img_file.lower():
        [ modality_type, modality_label, task ] = get_par_scan_tech(par_file=img_file, 
                                                                    search_dict=search_dict)
    elif '.nii' in img_file.lower():
        return "","",""
    else:
        return "","",""
    
    return (modality_type, 
            modality_label, 
            task)

def list_dir_files(pathname: str,
                    pattern: Optional[str] = "",
                    file_name_only: bool = False
                    ) -> List[str]:
    """List files and/or directories of some parent directory, in addition to pattern matched globbing if provided.

    NOTE:
        The output list is sorted.

    Usage example:
        >>> file_list = _list_dir_files(pathname='/<path>/<to>/<directory>',
        ...                             pattern='<filename>',
        ...                             file_name_only=False)
        ...

    Arguments:
        pathname: Pathname/directory path.
        pattern: Pattern to be matched should file globbing need to be performed.
        dir_file_name_only: If true, only the filenames are returned.

    Returns:
        List of strings that consists of files or file paths.

    Raises:
        FileNotFoundError: Error that arises if the pattern matched file or directory does not exist.
    """
    if os.path.exists(pathname):
        os.path.abspath(pathname)
    else:
        raise FileNotFoundError("Filepath does not exist.")
    
    if pattern:
        search: str = os.path.join(pathname,f"{pattern}")
    else:
        search: str = pathname
    
    if file_name_only:
        path_sep: str = os.path.sep
        file_dir_list: List[str] = [ x.replace(pathname + path_sep,'') for x in glob.glob(pathname=search) ]
        file_dir_list.sort()
        return file_dir_list
    else:
        file_dir_list: List[str] = glob.glob(pathname=search)
        file_dir_list.sort()
        return file_dir_list
