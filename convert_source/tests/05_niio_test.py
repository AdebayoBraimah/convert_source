# -*- coding: utf-8 -*-
"""Tests for the imgio's niio module's functions.

NOTE: Unable to reliably write NIFTI header information.
"""
import pytest

import os
import sys
import pathlib

from typing import List

# Add package/module to PYTHONPATH
mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(__file__)).parents[2]))
sys.path.append(mod_path)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    collect_info
)

from convert_source.imgio.niio import (
    get_num_frames,
    get_nii_tr
)

# Test variables
data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__),'test.study_dir'))
nii_test_data: str = os.path.join(data_dir,'TEST001-UNIT001','data.nifti')

# Begin tests
def test_collect_data():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm",".PAR"])

    sub: str = subs_data[0].sub
    ses: str = subs_data[0].ses

    assert len(subs_data) == 7
    assert sub == 'TEST001'
    assert ses == 'UNIT001'

def test_get_nii_tr():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm",".PAR"])

    assert get_nii_tr(subs_data[6].data) == 0.893

def test_get_num_frames():
    subs_data: List[SubDataInfo] = collect_info(parent_dir=data_dir,
                                                exclusion_list=[".dcm",".PAR"])

    assert get_num_frames(subs_data[6].data) == 500

##############################################################
#
# Code to create empty test NIFTI-2 files
#
##############################################################
# 
# NOTE: Unable to reliabely set NIFTI header information.
# 
# nii_list: List[str] = ['T1_AXIAL','T2_InPlane','DWI_68_DIR','rs_fMRI','rsfMRI','DWI_B0','FLAIR']
# 
# def create_nifti_image(name: str,
#                        num_frames: Optional[int] = 1,
#                        tr: Optional[float] = 2.00,
#                        task: Optional[str] = ""
#                        ) -> Tuple[str,str]:
#     '''Creates an empty NIFTI-2 image using the specified repetition time (TR, in sec.), and number of frames (/TRs).
#     A corresponding JSON sidecar is also created for the NIFTI-2 file.
# 
#     Usage example:
#         >>> [nii,json] = create_nifti_image("test.nii.gz")
# 
#     Arguments:
#         name: Output NIFTI-2 filename.
#         num_frames: Number of frames/TRs for the file to have.
#         tr: Repetition time (s)
#         task: Task name (e.g. "Resting state", "N-back", etc.)
# 
#     Returns:
#         Tuple of strings that represent:
#             * File path to NIFTI-2 image as a string.
#             * File path to corresponding JSON sidecar.
#     '''
#     # Create empty NIFTI-2 file
#     data = np.arange(4*4*3).reshape(4,4,3)
#     new_image = nib.Nifti2Image(data, affine=np.eye(4))
#     img_header = new_image.header
# 
#     img_header['dim'][3] = num_frames
#     img_header['pixdim'][4] = tr
# 
#     nib.save(new_image, name)
# 
#     # Write JSON
#     params: Dict = {"RepetitionTime":tr}
# 
#     if task:
#         tmp_dict: Dict = {"TaskName":task}
#         params.update(tmp_dict)
# 
#     # File class context manager to get filename for JSON file
#     with File(name) as f:
#         [path, filename, ext] = f.file_parts()
#         json_name: str = os.path.join(path,filename + ".json")
#   
#     json_name: str = write_json(json_file=json_name,
#                                 dictionary=params)
#
#     return (name,
#             json_name)
#
# def create_test_files(test_gzip: bool = False):
#     if test_gzip:
#         ext: str = '.nii.gz'
#     else:
#         ext: str = '.nii'
#
#     for nii in nii_list:
#         if 'dwi' in nii.lower():
#             num_frames: int = 68
#             tr: float = 1.2
#             task: str = ""
#         elif 'rsfMRI' in nii.lower():
#             num_frames: int = 500
#             tr: float = 1.00
#             task: str = "Resting State"
#         else:
#             num_frames: int = 1
#             tr: float = 0
#             task: str = ""
#       
#         nii_file: str = os.path.join(nii_test_data,nii + ".nii")
#
#         create_nifti_image(name=nii_file,
#                            num_frames=num_frames,
#                            tr=tr,
#                            task=task)
#
#         if 'dwi' in nii.lower():
#             with File(nii_file) as f:
#                 [path,filename,ext] = f.file_parts()
#
#                 bval: str = os.path.join(path,filename + ".bval")
#                 bvec: str = os.path.join(path,filename + ".bvec")
#
#                 with File(bval) as b:
#                     b.touch
#                     b.write_txt("0 0 0 0 0 800 1000 1500 2000 3000")
#                    
#                 with File(bvec) as e:
#                     e. touch()
# 
# if os.path.exists(os.path.join(nii_test_data,nii_list[0]+'.nii')) or os.path.exists(os.path.join(nii_test_data,nii_list[0]+'.nii.gz')):
#     pass
# else:
#     create_test_files(test_gzip=False)
# 
# CLI
# mod_path: str = os.path.join(str(pathlib.Path(os.path.abspath(os.getcwd())).parents[1]))
# sys.path.append(mod_path)
