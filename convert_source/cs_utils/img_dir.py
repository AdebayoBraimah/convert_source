# -*- coding: utf-8 -*-
"""Determines file paths of child directories that contain medical images, and their corresponding image types from some parent directory.
Currently supports use with: DICOM, PAR REC, and NIFTI files.
"""

import os
import glob

from typing import(
    List,
    Tuple
)

# Define function(s)
def id_img_file(dir_names: List[str],
                verbose: bool = False
                ) -> List[str]:
    """Creates list of file-types that either contain the label: DCM (``DICOM``), NII (``NIFTI``), PAR (``PAR REC``), or Unknown.
    
    Arguments:
        dir_names: Input directory names list.
        verbose: Enable verbose output.
    
    Returns:
        List of file-types that corresponds to input directory names list.
    """
    # Init empty list
    file_types: List[str] = list()
    
    # Iterate through directory names list
    for dir_name in dir_names:
        tmp_dir_par: List = glob.glob(os.path.join(dir_name,"*.PAR"))
        tmp_dir_nii: List = glob.glob(os.path.join(dir_name,"*.nii*"))
        tmp_dir_dcm: List = glob.glob(os.path.join(dir_name,"**","**","**","*.dcm"),recursive=True)

        if len(tmp_dir_dcm) > 0:
            if verbose:
                print("DCM")
            file_types.append("DCM")
        elif len(tmp_dir_nii) > 0:
            if verbose:
                print("NII")
            file_types.append("NII")
        elif len(tmp_dir_par) > 0:
            if verbose:
                print("PAR")
            file_types.append("PAR")
        else:
            if verbose:
                print("Unknown")
            file_types.append("Unknown")  

    return file_types

def img_dir_list(directory: str,
                 verbose: bool = False
                 ) -> Tuple[List[str],List[str]]:
    """Creates list of image file directories and file-types for some parent directy. The image file directories list
    is a sorted list consisting of unique file paths for each image file parent directory. The corresponding file-
    types list consists of labels that are: DCM (``DICOM``), NII (``NIFTI``), PAR (``PAR REC``), or Unknown - depending on the
    file-types in the image file parent directories.

    Usage example:
        >>> img_list, type_list = img_dir_list(img_dir)
    
    Arguments:
        directory: Parent directory that contains subject image data directories
        verbose: Enable verbose output

    Returns:
        Tuple:
            List of child directory names that contain image data.
            List of file-types that corresponds to directory names list.
    """
    # Init empty list
    dir_names: List[str] = list()

    # Recursively iterate through all files in directory - find parent directory of image files
    if verbose:
        print("Creating list of directories...")
    for root,dirnames,filenames in os.walk(directory, topdown=True, followlinks=True):
        if len(filenames) > 0:
            for file in filenames:
                if '._' in file:
                    # Skip hidden files if they exist.
                    continue
                if ('.dcm' in file.lower()) or ('.PAR' in file.upper()) or ('.nii' in file.lower()):
                    file_name: str = os.path.join(root,file)
                    if '.dcm' in file.lower():
                        dir_name: str = os.path.abspath(os.path.dirname(os.path.dirname(file_name)))
                    else:
                        dir_name: str= os.path.abspath(os.path.dirname(file_name))
                    # print(dir_name)
                    tmp_list: List[str] = [dir_name]
                    dir_names.extend(tmp_list)
                    
    # Create sorted list of unique directory paths
    if verbose:
        print("Creating unique list of directories...")
    dir_names: List[str] = list(set(dir_names))
    dir_names.sort()
    
    # Create file-type list
    if verbose:
        print("Identifying file types...")

    file_types = id_img_file(dir_names=dir_names,verbose=verbose)

    return dir_names,file_types

def list_to_file(in_list: List[str], 
                 out_file: str
                 ) -> str:
    """Writes some input list to some file.
    
    Arguments:
        in_list: List of subjects.
        out_file: Output filename.
    
    Returns:
        Output file with list written to file.
    """
    # Write list to file
    with open(out_file, "w") as f:
        for sub in in_list:
            # f.write("%s\n" % sub)
            f.write(f"{sub}\n")
        f.close()

    return out_file

def generate_img_list(directory: str,
                      out_prefix: str,
                      verbose: bool = False
                      ) -> Tuple[List[str],List[str],str,str]:
    """Generates list of image-containing directories and their corresponding image types from some parent directory. 
    The full path of the child directories that contain the images are written to file, in addition to their respective
    file types. The written files will contain '.dir_list.txt' and '.type_list.txt' appended to them.
    
    Arguments:
        directory: Input parent directory of that contain medical images somewhere in its directory structure.
        out_prefix: Output file prefix for written files.
        verbose: Enable verbosity.

    Returns:
        Tuple:
            * Child directories that contain medical images.
            * Corresponding file types to 'dir_names' list.
            * Output file that contains the contents of 'dir_names'.
            * Output file that contains the contents of 'file_types'.
    """
    # Generate directories list and child directories' file types
    [dir_names,file_types] = img_dir_list(directory=directory,verbose=verbose)
    
    # Write output files
    out_file_dir = list_to_file(in_list=dir_names,out_file=out_prefix + ".dir_list.txt")
    out_file_type = list_to_file(in_list=file_types,out_file=out_prefix + ".type_list.txt")
    
    return dir_names,file_types,out_file_dir,out_file_type
