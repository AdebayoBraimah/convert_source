# -*- coding: utf-8 -*-
"""Batch conversion wrapper and its associated classes and functions for the `convert_source` package.

TODO:
    * Update dcm2niix wrapper function to include all args.
        * Either collect and pass args with dicrtionary.
            OR
        * Use a yaml file to pass the args.
    * Write unit tests.
    * Resolve TODO's.
"""
import os
import glob
import yaml

from copy import deepcopy
from shutil import copy

from typing import (
    List, 
    Dict, 
    Optional, 
    Union, 
    Tuple
)

from convert_source.cs_utils.const import (
    DEFAULT_CONFIG,
    BIDS_PARAM
)

from convert_source.cs_utils.fileio import (
    ConversionError,
    NiiFile,
    LogFile,
    TmpDir
)

from convert_source.cs_utils.utils import (
    SubDataInfo,
    depth,
    list_dict,
    read_json,
    write_json,
    get_bvals,
    comp_dict,
    gzip_file,
    gunzip_file,
    list_in_substr,
    header_search,
    collect_info,
    get_metadata,
    convert_image_data,
    dict_multi_update
)

from convert_source.cs_utils.bids_info import (
    construct_bids_dict,
    construct_bids_name,
    search_bids
)

from convert_source.imgio.niio import (
    get_data_params,
    get_num_frames
)

# Define class(es)
class BIDSImgData(object):
    '''Class that creates an object of lists for a set of image data,
    and its associated (BIDS related) files - allows for grouping of 
    image data and its associated files.

    Attributes (instance attributes):
        imgs: List of image files. Emtpy when initialized.
        jsons: List of corresponding JSON files. Emtpy when initialized.
        bvals: List of corresponding bval files. Emtpy when initialized.
        bvecs: List of corresponding bvec files. Emtpy when initialized.
    '''
    def __init__(self,
                 imgs: Optional[str] = "",
                 jsons: Optional[str] = "",
                 bvals: Optional[str] = "",
                 bvecs: Optional[str] = ""
                ):
        '''Init doc-string for BIDSImgData class. Allows
        for grouping of image data and its associated files.

        Usage example:
            >>> data_obj = BIDSImgData(img,
            ...                        json)
            ...

        Arguments:
            imgs: Input image.
            jsons: Corresponding input JSON file.
            bvals: Corresponding input FSL-style bval file.
            bvecs: Corresponding input FSL-style bvec file.
        '''
        if imgs:
            self.imgs: List = [imgs]
        else:
            self.imgs: List = []
        
        if jsons:
            self.jsons: List = [jsons]
        else:
            self.jsons: List = []
        
        if bvals:
            self.bvals: List = [bvals]
        else:
            self.bvals: List = []
                
        if bvecs:
            self.bvecs: List = [bvecs]
        else:
            self.bvecs: List = []
    
    def __repr__(self):
        '''NOTE: Returns Dictionary of key-value mapped lists,
        represented as a string.
        '''
        return (str(
                {"imgs":self.imgs,
                "jsons":self.jsons,
                "bvals":self.bvals,
                "bvecs":self.bvecs})
               )

    def add(self,
            imgs: Optional[Union[List[str],str]] = "",
            jsons: Optional[Union[List[str],str]] = "",
            bvals: Optional[Union[List[str],str]] = "",
            bvecs: Optional[Union[List[str],str]] = ""
            ) -> Tuple[List[str],List[str],List[str],List[str]]:
        '''Extends or appends to a list depending on if a list or string is passed as an argument.

        Usage example:
            >>> data_obj = BIDSImgData(img,
            ...                        json)
            ...
            >>> data_obj.add(imgs=[img1,img2],
            ...              jsons=[json1,''])
            ...

        Arguments:
            imgs: Input NIFTI image OR list of NIFTI image files.
            jsons: Corresponding JSON file OR list of corresponding JSON files.
            bvals: Corresponding bval file OR list of corresponding bval files.
            bvecs: Corresponding bvec file OR list of corresponding bvec files.

        Returns:
            Tuple of four lists that consists of:
                * Image files
                * Corresponding JSON files
                * Corresponding bval files
                * Corresponding bvec files
        '''
        if imgs:
            self.imgs.extend(imgs)
        else:
            self.imgs.append("")
        
        if jsons:
            self.jsons.extend(jsons)
        else:
            self.jsons.append("")
        
        if bvals:
            self.bvals.extend(bvals)
        else:
            self.bvals.append("")
        
        if bvecs:
            self.bvecs.extend(bvecs)
        else:
            self.bvecs.append("")
        
        return (self.imgs,
                self.jsons,
                self.bvals,
                self.bvecs)

# Define function(s)
def read_config(config_file: Optional[str] = "", 
                verbose: Optional[bool] = False
                ) -> Tuple[Dict[str,str],Dict,Dict,Dict,List[str]]:
    '''Reads configuration file and creates a dictionary of search terms for 
    each modality provided that each BIDS modality is used as a key via the 
    keyword 'modality_search'. Should BIDS related parameter descriptions need 
    to be used when renaming files, the related search and mapping terms can included 
    via the keywords 'bids_search' and 'bids_map', respectively. If these keywords 
    are not specified, then empty dictionaries are returned. Should exclusions be provided 
    (via the key 'exclude') then an exclusion list is created. Should this not be provided, 
    then an empty list is returned.

    BIDS modalities:
        - anat:
            - T1w, T2w, FLAIR, etc.
        - func:
            - bold
                - task:
                    - resting state, <task-name>
        - dwi
        - fmap

    Usage example:
        >>> [search_dict, bids_search, bids_map, meta_dict, exclusion_list] = read_config(config_file)
    
    Arguments:
        config_file: File path to yaml configuration file. If no file is used, then the default configuration file is used.
        verbose: Prints additional information to screen.
    
    Returns: 
        Tuple of dictionaries and a list that consists of:
            * search_dict: Nested dictionary of heuristic modality search terms for BIDS modalities.
            * bids_search: Nested dictionary of heuristic BIDS search terms.
            * bids_map: Corresponding nested dictionary of BIDS mapping terms to rename files to.
            * meta_dict: Nested dictionary of metadata terms to write to JSON file(s).
            * exclusion_list: List of exclusion terms.
    
    Raises:
        ConfigFileReadError: Error that arises if no heuristic search terms are provided.
    '''
    class ConfigFileReadError(Exception):
        pass

    if config_file:
        config_file: str = os.path.abspath(config_file)
    else:
        config_file: str = DEFAULT_CONFIG

    with open(config_file) as file:
        data_map: Dict[str,str] = yaml.safe_load(file)
        if verbose:
            print("Initialized parameters from configuration file")
    
    # Required modality search terms
    if any("modality_search" in data_map for element in data_map):
        if verbose:
            print("Categorizing search terms")
        search_dict: Dict[str,str] = data_map["modality_search"]
    else:
        if verbose:
            print("Heuristic search terms required. Exiting...")
        raise ConfigFileReadError("Heuristic search terms required. Exiting...")
    
    # BIDS search terms
    if any("bids_search" in data_map for element in data_map):
        if verbose:
            print("Including BIDS related search term settings")
        bids_search: Dict[str,str] = data_map["bids_search"]
    else:
        if verbose:
            print("No BIDS related search term settings")
        meta_dict: Dict = dict()
    
    # BIDS mapping terms
    if any("bids_map" in data_map for element in data_map):
        if verbose:
            print("Corresponding BIDS mapping settings")
        bids_map: Dict[str,str] = data_map["bids_map"]
    else:
        if verbose:
            print("No BIDS mapping settings")
        meta_dict: Dict = dict()
    
    # Metadata terms
    if any("metadata" in data_map for element in data_map):
        if verbose:
            print("Including additional settings for metadata")
        meta_dict: Dict[str,Union[str,int]] = data_map["metadata"]
    else:
        if verbose:
            print("No metadata settings")
        meta_dict: Dict = dict()
    
    # Exclusion terms/terms to ignore
    if any("exclude" in data_map for element in data_map):
        if verbose:
            print("Exclusion option implemented")
        exclusion_list: List[str] = data_map["exclude"]
    else:
        if verbose:
            print("Exclusion option not implemented")
        exclusion_list: List = list()
        
    return (search_dict,
            bids_search,
            bids_map,
            meta_dict,
            exclusion_list)

def bids_id(s:str,
            search_dict: Dict,
            bids_search: Optional[Dict] = None,
            bids_map: Optional[Dict] = None,
            bids_name_dict: Optional[Dict] = None,
            parent_dir: Optional[str] = "",
            modality_type: Optional[str] = "",
            modality_label: Optional[str] = "",
            task: Optional[str] = ""
           ) -> Tuple[Dict[str,str],str,str,str]:
    '''Performs identification of descriptive BIDS information relevant for file naming, provided
    a BIDS search dictionary and a BIDS map dictionary. The resulting information is then placed
    in nested dictionary of BIDS related descriptive terms.
    
    Usage example:
        >>> bids_example_dict = bids_id("ImageFile00001.dcm")
        
    Arguments:
        s: Input str/file to be searched.
        search_dict: Dictionary of modality specific search terms.
        bids_search: Dictionary of BIDS specific search terms.
        bids_map: Dictionary of BIDS related terms to be mapped to BIDS search terms.
        bids_name_dict: Existing BIDS name dictionary. If provided, an updated copy of this dictionary is returned.
        parent_dir: Parent or study image directory of the image file. This path is removed from the string search
            to prevent false positives.
        modality_type: (BIDS) modality type (e.g. 'anat', 'func', etc).
        modality_label: (BIDS) modality label (e.g. 'T1w', 'bold', etc).
        task: (BIDS) task label (e.g. 'rest','nback', etc).
        
    Returns:
        Tuple that consists of:
            * Nested dictionary of BIDS descriptive naming related terms.
            * Modality type.
            * Modality label.
            * Task label.
    '''
    search_arr: List[str] = list_dict(d=search_dict)
    
    if os.path.exists(s) and parent_dir:
        # Store string, then overwrite
        img_file_path:str = s
        path_sep: str = os.path.sep
        s: str = s.replace(parent_dir + path_sep,"")
    else:
        img_file_path:str = s
    
    if bids_name_dict:
        bids_name_dict: Dict = deepcopy(bids_name_dict)
    else:
        bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    
    mod_found: bool = False
    
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
                    if list_in_substr(in_list=mod_search,in_str=s):
                        mod_found: bool = True
                        modality_type: str = mod_type
                        modality_label: str = mod_label
                        task: str = mod_task
                        bids_name_dict: Dict = search_bids(s=s,
                                                           bids_search=bids_search,
                                                           bids_map=bids_map,
                                                           modality_type=modality_type,
                                                           modality_label=modality_label,
                                                           bids_name_dict=bids_name_dict)
                            
            elif depth(i) == 4:
                for k2,v2 in v.items():
                    for k3,v3 in v2.items():
                        mod_type: str = k
                        mod_label: str = k2
                        mod_task: str = k3
                        mod_search: List[str] = v3
                        if list_in_substr(in_list=mod_search,in_str=s):
                            mod_found: bool = True
                            modality_type: str = mod_type
                            modality_label: str = mod_label
                            task: str = mod_task
                            bids_name_dict: Dict = search_bids(s=s,
                                                               bids_search=bids_search,
                                                               bids_map=bids_map,
                                                               modality_type=modality_type,
                                                               modality_label=modality_label,
                                                               task=task,
                                                               bids_name_dict=bids_name_dict)

    # Contingency search if initially unsuccessful
    if mod_found:
        pass
    else:
        [modality_type, modality_label, task] = header_search(img_file=img_file_path,
                                                              search_dict=search_dict)
        # Back track if modality type and label were found
        if modality_type and modality_label:
            [bids_name_dict,
             modality_type,
             modality_label,
             task] = bids_id(s=img_file_path,
                             search_dict=search_dict,
                             bids_search=bids_search,
                             bids_map=bids_map,
                             bids_name_dict=bids_name_dict,
                             parent_dir=parent_dir,
                             modality_type=modality_type,
                             modality_label=modality_label,
                             task=task)
    
    return (bids_name_dict,
            modality_type,
            modality_label,
            task)

def _gather_bids_name_args(bids_name_dict: Dict,
                           modality_type: str,
                           param: str
                          ) -> Union[str,bool]:
    '''Helper function that gathers BIDS naming description arguments for the `construct_bids_name` function. In the case that 'fmap' is passed as the 
    'modality_type' argument, then the 'param' argument must be either: 'mag2', 'case1', 'case2', 'case3', or 'case4'.
    
    Usage example:
        >>> param_name = _gather_bids_name_args(bids_dict,
        ...                                     "anat",
        ...                                     "ce")
        ...
        
    Arguments:
        bids_name_dict: BIDS name description dictionary.
        modality_type: Modality type.
        param: BIDS parameter description.
    
    Returns:
        String from the BIDS name description dictionary if it exists, or an empty string otherwise. In the case of 'fmap', then a boolean value is returned.
    '''
    if modality_type.lower() == 'fmap' and (param == "case1" or param == "mag2" or param == "case2" or param == "case3" or param == "case4"):
        if param == 'mag2':
            param = 'case1'
            if bids_name_dict[modality_type][param].get('magnitude2',''):
                return True
            else:
                return False
        elif param == 'case1':
            if bids_name_dict[modality_type][param].get('phasediff',''):
                return True
            else:
                False
        elif param == 'case2':
            if bids_name_dict[modality_type][param].get('phase1',''):
                return True
            else:
                return False
        elif param == 'case3':
            if bids_name_dict[modality_type][param].get('fieldmap',''):
                return True
            else:
                return False
        elif param == 'case4':
            if bids_name_dict[modality_type][param].get('modality_label',''):
                return True
            else:
                return False
    else:
        return bids_name_dict[modality_type].get(param,'')

def _get_bids_name_args(bids_name_dict: Dict,
                        modality_type: str
                        ) -> Tuple[str,bool]:
    '''Helper function that wraps the funciton `_gather_bids_name_args`.
    
    Usage example:
        >>> param_tuple = _get_bids_name_args(bids_dict,
        ...                                   'anat')
        ...

    Arguments:
        bids_name_dict: BIDS name description dictionary.
        modality_type: Modality type.

    Returns:
        Tuple of strings and booleans that represent:
            * task: str, task name BIDS filename description.
            * acq: str, acquisition description.
            * ce: str, contrast enhanced description
            * acq_dir: str, acquisition direction description.
            * rec: str, reconstruction methods description.
            * echo: str, echo number description from multi-echo acquisition.
            * case1: bool, fieldmap BIDS case 1.
            * mag2: bool, fieldmap BIDS case 1, that includes 2nd magnitude image.
            * case2: bool, fieldmap BIDS case 2.
            * case3: bool, fieldmap BIDS case 3.
            * case4: bool, fieldmap BIDS case 4.
    '''
    task: str = ""
    acq: str = ""
    ce: str = ""
    acq_dir: str = ""
    rec: str = ""
    echo: str = ""
    case1: bool = False
    mag2: bool = False
    case2: bool = False
    case3: bool = False
    case4: bool = False

    params_var: List[str] = [task, acq, ce, acq_dir, rec, echo, case1, mag2, case2, case3, case4]
    params_str: List[str] = ["task", "acq", "ce", "acq_dir", "rec", "echo", "case1", "mag2", "case2", "case3", "case4"]

    if len(params_str) == len(params_var):
        pass
    else:
        raise IndexError("Paired arrays of two different lengths are being compared.")

    for i in range(0,len(params_var)):
        params_var[i] = _gather_bids_name_args(bids_name_dict=bids_name_dict,
                                               modality_type=modality_type,
                                               param=params_str[i])

    return tuple(params_var)

def make_bids_name(bids_name_dict: Dict,
                    modality_type: str
                   ) -> Tuple[str,str,str,str]:
    '''Creates a BIDS compliant filename given a BIDS name description dictionary, and the modality type.

    Usage example:
        >>> make_bids_name(bids_name_dict=bids_dict,
        ...                 modality_type="anat")
        ...
        "sub-001_ses-001_run-01_T1w"
        
    Arguments:
        bids_name_dict: BIDS name description dictionary.
        modality_type: Modality type.

    Returns:
        BIDS compliant filename string.
    '''
    
    bids_keys: List[str] = list(bids_name_dict[modality_type].keys())
    
    sub: str = bids_name_dict['info']['sub']
    ses: str = bids_name_dict['info']['ses']
    run: Union[int,str] = bids_name_dict[modality_type]['run']

    [task, 
     acq, 
     ce, 
     acq_dir, 
     rec, 
     echo, 
     case1, 
     mag2, 
     case2, 
     case3, 
     case4] = _get_bids_name_args(bids_name_dict=bids_name_dict,
                                  modality_type=modality_type)
    
    f_name: str = ""
    f_name += f"sub-{sub}"
    
    if ses:
        f_name += f"_ses-{ses}"
    
    if task and ('task' in bids_keys):
        f_name += f"_task-{task}"
    
    if acq and ('acq' in bids_keys):
        f_name += f"_acq-{acq}"
    
    if ce and ('ce' in bids_keys):
        f_name += f"_ce-{ce}"
    
    if acq_dir and ('dir' in bids_keys):
        f_name += f"_dir-{acq_dir}"
    
    if rec and ('rec' in bids_keys):
        f_name += f"_rec-{rec}"

    f_name += f"_run-{run}"

    if echo and ('echo' in bids_keys):
        f_name += f"_echo-{echo}"
    
    if modality_type.lower() == 'fmap':
        if case1 and mag2:
            f_name1: str = f_name + "_phasediff"
            f_name2: str = f_name + "_magnitude1"
            f_name3: str = f_name + "_magnitude2"
            return (f_name1,
                   f_name2,
                   f_name3,
                   "")
        elif case1:
            f_name1: str = f_name + "_phasediff"
            f_name2: str = f_name + "_magnitude1"
            return (f_name1,
                   f_name2,
                   "",
                   "")
        elif case2:
            f_name1: str = f_name + "_phase1"
            f_name2: str = f_name + "_phase2"
            f_name3: str = f_name + "_magnitude1"
            f_name4: str = f_name + "_magnitude2"
            return (f_name1,
                   f_name2,
                   f_name3,
                   f_name4)
        elif case3:
            f_name1: str = f_name + "_magnitude"
            f_name2: str = f_name + "_fieldmap"
            return (f_name1,
                   f_name2,
                   "",
                   "")
        elif case4:
            modality_label = bids_name_dict[modality_type]['modality_label']
            f_name += f"_{modality_label}"
            return f_name,"","",""
    else:
        modality_label = bids_name_dict[modality_type]['modality_label']
        f_name += f"_{modality_label}"
        return f_name,"","",""

def source_to_bids(sub_data: SubDataInfo,
                   bids_name_dict: Dict,
                   out_dir: str,
                   modality_type: Optional[str] = "",
                   modality_label: Optional[str] = "",
                   task: Optional[str] = "",
                   meta_dict: Optional[Dict] = {},
                   mod_dict: Optional[Dict] = {},
                   gzip: bool = True,
                   append_dwi_info: bool = True,
                   zero_pad: int = 2,
                   cprss_lvl: int = 6,
                   verbose: bool = False,
                   log: Optional[LogFile] = None,
                   env: Optional[Dict] = {},
                   dryrun: bool = False
                   ) -> Tuple[List[str],List[str],List[str],List[str]]:
    '''
    TODO:
        * Write documentation.
    
    Converts source data to BIDS raw data.
    '''
    sub: Union[int,str] = sub_data.sub
    ses: Union[int,str] = sub_data.ses
    data: str = sub_data.data
    
    sub_dir: str = os.path.join(out_dir,"sub-" + sub)
    sub_tmp: str = sub_dir
    
    if ses:
        sub_dir: str = os.path.join(sub_dir,"ses-" + ses)

    # Gather BIDS name description args
    [task, 
     acq, 
     ce, 
     acq_dir, 
     rec, 
     echo, 
     case1, 
     mag2, 
     case2, 
     case3, 
     case4] = _get_bids_name_args(bids_name_dict=bids_name_dict,
                                  modality_type=modality_type)

    # Using TmpDir and TmpFile context managers
    with TmpDir(tmp_dir=sub_tmp,use_cwd=False) as tmp:
        with TmpDir.TmpFile(tmp_dir=tmp.tmp_dir) as f:
            tmp.mk_tmp_dir()
            [_path, basename, _ext] = f.file_parts()
            try:
                img_data = convert_image_data(file=data,
                                              basename=basename,
                                              out_dir=tmp.tmp_dir,
                                              gzip=gzip,
                                              cprss_lvl=cprss_lvl,
                                              verbose=verbose,
                                              log=log,
                                              env=env,
                                              dryrun=dryrun,
                                              return_obj=True)

                # Update JSON files
                for i in range(0,len(img_data.imgs)):
                    if img_data.jsons[i]:
                        json_dict: Dict = read_json(json_file=img_data.jsons[i])

                        param_dict: Dict = get_data_params(file=data,
                                                           json_file=img_data.jsons[i])

                        metadata: Dict = dict_multi_update(dictionary=None,
                                                           **meta_dict,
                                                           **param_dict,
                                                           **mod_dict)

                        bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                              json_dict=json_dict)

                        img_data.jsons[i] = write_json(json_file=img_data.jsons[i],
                                                            dictionary=bids_dict)

                        if (modality_type.lower() == 'dwi' or modality_label.lower() == 'dwi') and append_dwi_info:
                            bvals: List[int] = get_bvals(img_data.bvals[i])
                            echo_time: int = bids_dict["EchoTime"] * 1000
                            _label: str = ""
                            for bval in bvals:
                                if bval != 0:
                                    _label += f"b{bval}"
                            _label += f"TE{echo_time}"
                            if acq:
                                acq += _label
                            else:
                                acq = _label
                
                # BIDS 'fmap' cases
                case1: bool = False
                case2: bool = False
                case3: bool = False
                case4: bool = False
                mag2: bool = False
                
                if modality_type.lower() == 'fmap':
                    if len(img_data.imgs) == 4:
                        case2: bool = True
                    elif len(img_data.imgs) == 3:
                        case1: bool = True
                        mag2: bool = True
                    elif len(img_data.imgs) == 1:
                        case4 = True
                    elif len(img_data.imgs) == 2:
                        for i in img_data.imgs:
                            # This needs more review, need to know output of fieldmaps from dcm2niix
                            if list_in_substr(['mag','map','a'],i):
                                case3: bool = True
                                break
                            else:
                                case1: bool = True
                
                if modality_type:    
                    out_data_dir: str = os.path.join(sub_dir, modality_type)
                else:
                    out_data_dir: str = os.path.join(out_dir, "unknown")
                
                if modality_type.lower() == 'dwi' or modality_type.lower() == 'func' :
                    num_frames = get_num_frames(img_data.imgs[0])
                    if num_frames == 1:
                        modality_label: str = "sbref"
                
                # Re-write BIDS name dictionary and update to reflect NIFTI data
                bids_name_dict: Dict = construct_bids_name(sub_data=sub_data,
                                                           modality_type=modality_type,
                                                           modality_label=modality_label,
                                                           acq=acq,
                                                           ce=ce,
                                                           task=task,
                                                           acq_dir=acq_dir,
                                                           rec=rec,
                                                           echo=echo,
                                                           case1=case1,
                                                           mag2=mag2,
                                                           case2=case2,
                                                           case3=case3,
                                                           case4=case4,
                                                           zero_pad=zero_pad,
                                                           out_dir=out_data_dir)

                # Ensure that DWI and Fieldmap data are not kept as unknown
                # by back-tracking if that is the case.
                if img_data.bvals[0] and img_data.bvecs[0] and not modality_type:
                    modality_type = 'dwi'
                    modality_label = 'dwi'
                    sub_data.data = img_data.imgs[0]
                    # Recursive function call here
                elif len(img_data.imgs) >= 2 and not modality_type:
                    modality_type = 'fmap'
                    modality_label = 'fmap'
                    sub_data.data = img_data.imgs[0]
                    # Recursive function call here

                if os.path.exists(out_data_dir):
                    pass
                else:
                    os.makedirs(out_data_dir)

                if modality_type:
                    pass
                else:
                    modality_type: str = "unknown"
                
                [bids_1, bids_2, bids_3, bids_4] = make_bids_name(bids_name_dict=bids_name_dict,
                                                                   modality_type=modality_type)

                bids_names: List[str] = [bids_1, bids_2, bids_3, bids_4]
                
                # Image data return lists
                imgs: List[str] = []
                jsons: List[str] = []
                bvals: List[str] = []
                bvecs: List[str] = []
                
                for i in range(0,len(img_data.imgs)):
                    out_name: str = ""
                    if gzip:
                        ext: str = ".nii.gz"
                    else:
                        ext: str = ".nii"
                    
                    out_name: str = os.path.join(out_data_dir,bids_names[i])

                    out_nii: str = out_name + ext
                    out_json: str = out_name + ".json"
                    out_bval: str = out_name + ".bval"
                    out_bvec: str = out_name + ".bvec"

                    out_nii = copy(img_data.imgs[i],out_nii)
                    imgs.append(out_nii)

                    if img_data.jsons[i]:
                        out_json = copy(img_data.jsons[i],out_json)
                        jsons.append(out_json)
                    else:
                        jsons.append("")
                    
                    if img_data.bvals[i]:
                        out_bval = copy(img_data.bvals[i],out_bval)
                        bvals.append(out_bval)
                    else:
                        bvals.append("")
                    
                    if img_data.bvecs[i]:
                        out_bvec = copy(img_data.bvecs[i],out_bvec)
                        bvecs.append(out_bvec)
                    else:
                        bvecs.append("")
                # Clean-up
                tmp.rm_tmp_dir()
                return (imgs,
                        jsons,
                        bvals,
                        bvecs)
            except ConversionError:
                tmp.rm_tmp_dir()
                return [""],[""],[""],[""]

def nifti_to_bids(sub_data: SubDataInfo,
                  bids_name_dict: Dict,
                  out_dir: str,
                  modality_type: Optional[str] = "",
                  modality_label: Optional[str] = "",
                  task: Optional[str] = "",
                  meta_dict: Optional[Dict] = {},
                  mod_dict: Optional[Dict] = {},
                  gzip: bool = True,
                  append_dwi_info: bool = True,
                  zero_pad: int = 2,
                  cprss_lvl: int = 6,
                  verbose: bool = False,
                  log: Optional[LogFile] = None,
                  env: Optional[Dict] = {},
                  dryrun: bool = False
                  ) -> Tuple[List[str],List[str],List[str],List[str]]:
    '''
    TODO: 
        * write documentation

    Converts existing NIFTI data to BIDS raw data.
    '''
    sub: Union[int,str] = sub_data.sub
    ses: Union[int,str] = sub_data.ses
    data: str = sub_data.data
    
    sub_dir: str = os.path.join(out_dir,"sub-" + sub)
    sub_tmp: str = sub_dir
    
    if ses:
        sub_dir: str = os.path.join(sub_dir,"ses-" + ses)

    # Gather BIDS name description args
    [task, 
     acq, 
     ce, 
     acq_dir, 
     rec, 
     echo, 
     case1, 
     mag2, 
     case2, 
     case3, 
     case4] = _get_bids_name_args(bids_name_dict=bids_name_dict,
                                  modality_type=modality_type)

    # Use NiiFile context manager
    with NiiFile(data) as n:
        [path, basename, ext] = n.file_parts()
        img_files: List[str] = glob.glob(os.path.join(path,basename + "*" + ext))
        json_file: str = os.path.join(path,basename + "*.json")
        bval_file: str = ''.join(glob.glob(os.path.join(path,basename + "*.bval*")))
        bvec_file: str = ''.join(glob.glob(os.path.join(path,basename + "*.bvec*")))
        
        if json_file:
            json_dict: Dict = read_json(json_file=json_file)

            param_dict: Dict = get_data_params(file=data,
                                               json_file=json_file)

            metadata: Dict = dict_multi_update(dictionary=None,
                                               **meta_dict,
                                               **param_dict,
                                               **mod_dict)

            bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                  json_dict=json_dict)
        else:
            json_dict: Dict = read_json(json_file="")
            metadata: Dict = dict_multi_update(dictionary=None,
                                               **meta_dict,
                                               **mod_dict)
            
            bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                  json_dict=json_dict)

        # BIDS 'fmap' cases
        case1: bool = False
        case2: bool = False
        case3: bool = False
        case4: bool = False
        mag2: bool = False
        
        if modality_type.lower() == 'fmap':
            if len(img_files) == 4:
                case2: bool = True
            elif len(img_files) == 3:
                case1: bool = True
                mag2: bool = True
            elif len(img_files) == 1:
                case4 = True
            elif len(img_files) == 2:
                for i in img_files:
                    # This needs more review, need to know output of fieldmaps from dcm2niix
                    if list_in_substr(['mag','map','a'],i):
                        case3: bool = True
                        break
                    else:
                        case1: bool = True
        
        if modality_type.lower() == 'dwi' or modality_type.lower() == 'func' :
            num_frames = get_num_frames(img_files[0])
            if num_frames == 1:
                modality_label: str = "sbref"

        if (modality_type.lower() == 'dwi' or modality_label.lower() == 'dwi') and append_dwi_info:
            bvals: List[int] = get_bvals(bval_file)
            echo_time: Union[int,str] = bids_dict["EchoTime"] * 1000
            _label: str = ""
            for bval in bvals:
                if bval != 0:
                    _label += f"b{bval}"
            if echo_time:
                _label += f"TE{echo_time}"
            if acq:
                acq += _label
            else:
                acq = _label

        if modality_type:    
            out_data_dir: str = os.path.join(sub_dir, modality_type)
        else:
            out_data_dir: str = os.path.join(out_dir, "unknown")

        # Re-write BIDS name dictionary and update to reflect NIFTI data
        bids_name_dict: Dict = construct_bids_name(sub_data=sub_data,
                                                    modality_type=modality_type,
                                                    modality_label=modality_label,
                                                    acq=acq,
                                                    ce=ce,
                                                    task=task,
                                                    acq_dir=acq_dir,
                                                    rec=rec,
                                                    echo=echo,
                                                    case1=case1,
                                                    mag2=mag2,
                                                    case2=case2,
                                                    case3=case3,
                                                    case4=case4,
                                                    zero_pad=zero_pad,
                                                    out_dir=out_data_dir)

        if os.path.exists(out_data_dir):
            pass
        else:
            os.makedirs(out_data_dir)

        if modality_type:
            pass
        else:
            modality_type: str = "unknown"
        
        [bids_1, bids_2, bids_3, bids_4] = make_bids_name(bids_name_dict=bids_name_dict,
                                                           modality_type=modality_type)
        
        bids_names: List[str] = [bids_1, bids_2, bids_3, bids_4]
        
        # Image data return lists
        imgs: List[str] = []
        jsons: List[str] = []
        bvals: List[str] = []
        bvecs: List[str] = []
        
        for i in range(0,len(img_files)):
            out_name: str = os.path.join(out_data_dir,bids_names[i])

            out_nii: str = out_name + ext
            out_json: str = out_name + ".json"
            out_bval: str = out_name + ".bval"
            out_bvec: str = out_name + ".bvec"

            out_nii = copy(img_files[i],out_nii)
            out_json = write_json(json_file=out_json,
                                  dictionary=bids_dict)
            
            if gzip and ('.nii.gz' in out_nii):
                pass
            elif (not gzip) and ('.nii.gz' in out_nii):
                out_nii = gunzip_file(file=out_nii,
                                      native=True)
            elif gzip and ('.nii' in out_nii):
                out_nii = gzip_file(file=out_nii,
                                    native=True)
            
            imgs.append(out_nii)
            jsons.append(out_json)
            
            if bval_file and bvec_file:
                out_bval = copy(bval_file,out_bval)
                out_bvec = copy(bvec_file,out_bvec)
                bvals.append(out_bval)
                bvecs.append(out_bvec)
            else:
                out_bval: str = ""
                out_bvec: str = ""
                bvals.append("")
                bvecs.append("")
    
        return (imgs,
                jsons,
                bvals,
                bvecs)

def data_to_bids(sub_data: SubDataInfo,
                 bids_name_dict: Dict,
                 out_dir: str,
                 modality_type: Optional[str] = "",
                 modality_label: Optional[str] = "",
                 task: Optional[str] = "",
                 meta_dict: Optional[Dict] = {},
                 mod_dict: Optional[Dict] = {},
                 gzip: bool = True,
                 append_dwi_info: bool = True,
                 zero_pad: int = 2,
                 cprss_lvl: int = 6,
                 verbose: bool = False,
                 log: Optional[LogFile] = None,
                 env: Optional[Dict] = {},
                 dryrun: bool = False
                 ) -> Tuple[List[str],List[str],List[str],List[str]]:
    '''Converts source data to BIDS compliant data. This functions also
    renames already existing NIFTI data so that it can be BIDS compliant.
    
    Usage example:
        >>> [imgs, jsons, bvals, bvecs] = data_to_bids(sub_obj,
        ...                                            bids_name_dict,
        ...                                            output_dir,
        ...                                            'anat',
        ...                                            'T1w')
        ...

    Arguments:
        sub_data: Subject data information object.
        bids_name_dict: BIDS name dictionary.
        out_dir: Output directory.
        modality_type: Modality type (BIDS label e.g. 'anat', 'func', etc).
        modality_label: Modality label (BIDS label  e.g. 'T1w', 'bold', etc).
        task: Task label (BIDS filename task label, e.g. 'rest', 'nback', etc.)
        meta_dict: BIDS common metadata dictoinary.
        mod_dict: Modality specific metadata dictionary.
        gzip: Gzip output NIFTI files.
        append_dwi_info: Appends DWI acquisition information (unique non-zero b-values, and TE, in msec.) to BIDS acquisition filename.
        zero_pad: Number of zeroes to pad the run number up to (zero_pad=2 is '01').
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest (dcm2niix option).
        verbose: Enable verbose output (dcm2niix option).
        log: LogFile object for logging.
        env: Path environment dictionary.
        dryrun: Perform dryrun (creates the command, but does not execute it).

    Returns:
        Tuple of lists that contains:
            * List of image data file(s). Empty string is returned if this file does not exist.
            * List of corresponding JSON (sidecar) file(s). Empty string is returned if this file does not exist.
            * List of corresponding FSL-style bval file(s). Empty string is returned if this file does not exist.
            * List of corresponding FSL-style bvec file(s). Empty string is returned if this file does not exist.
    
    TODO: 
        * Init subject log file here.
        * Write log files for each subject.
            * BUG: logging class only writes to one file.
    '''
    if ('.dcm' in sub_data.data.lower()) or ('.par' in sub_data.data.lower()):
        source_to_bids() # Add args later
    elif '.nii' in sub_data.data.lower():
        nifti_to_bids() # Add args later
    else:
        return [""],[""],[""],[""]

def batch_proc(config_file: str,
              study_img_dir: str,
              out_dir: str,
              verbose: bool = False,
              return_obj: bool = False
              ) -> Union[List[BIDSImgData],Tuple[List[str]]]:
    '''Batch processes a study's source image data provided a configuration, the parent directory of the study's imaging data,
    and an output directory to place the BIDS NIFTI data.

    Usage example:
        >>> subs_bids_data = batch_proc(config_file,
        ...                             study_img_dir,
        ...                             out_dir)
        ...

    Arguments:
        config_file: Configuration file.
        study_img_dir: Path to study image parent directory that contains all the subjects' source image data.
        out_dir: Output directory.
        verbose: Verbose output.
        return_obj: Return a single object that is collection of lists, rather than a tuple of lists.

    Returns:
        Tuple of lists that consists of: 
            * List of NIFTI images.
            * Corresponding list of JSON sidecars.
            * Corresponding list of bval files.
            * Corresponding list of bvec files.

            OR 

        List of BIDSImgData objects. The BIDSImgData object that contains:
            * List of NIFTI images.
            * Corresponding list of JSON sidecars.
            * Corresponding list of bval files.
            * Corresponding list of bvec files.
    '''
    [search_dict,
     bids_search,
     bids_map,
     meta_dict,
     exclusion_list] = read_config(config_file=config_file,
                                   verbose=verbose)
    
    # Check BIDS searcn and map dictionaries
    if comp_dict(d1=bids_search,d2=bids_map):
        pass
    
    subs_data: List[SubDataInfo] = collect_info(parent_dir=study_img_dir,
                                                exclusion_list=exclusion_list)
    
    subs_bids: BIDSImgData = BIDSImgData()
       
    for sub_data in subs_data:
        data: str = sub_data.data
        bids_name_dict: Dict = deepcopy(BIDS_PARAM)
        bids_name_dict['info']['sub'] = sub_data.sub
        if sub_data.ses:
            bids_name_dict['info']['ses'] = sub_data.ses
        [bids_name_dict, 
         modality_type, 
         modality_label, 
         task] = bids_id(s=data,
                         search_dict=search_dict,
                         bids_search=bids_search,
                         bids_map=bids_map,
                         bids_name_dict=bids_name_dict,
                         parent_dir=study_img_dir)
        [meta_com_dict, 
         meta_scan_dict] = get_metadata(dictionary=meta_dict,
                                        modality_type=modality_type,
                                        task=task)
        # Convert source data
        [imgs,
         jsons,
         bvals,
         bvecs] = data_to_bids(sub_data=sub_data,
                               bids_name_dict=bids_name_dict,
                               out_dir=out_dir,
                               modality_type=modality_type,
                               modality_label=modality_label,
                               task=task,
                               meta_dict=meta_com_dict,
                               mod_dict=meta_scan_dict)

        # Collect data using BIDSImgData object
        subs_bids.add(imgs=imgs,
                      jsons=jsons,
                      bvals=bvals,
                      bvecs=bvecs)

    if return_obj:
        return subs_bids
    else:
        imgs: List[str] = subs_bids.imgs
        jsons: List[str] = subs_bids.jsons
        bvals: List[str] = subs_bids.bvals
        bvecs: List[str] = subs_bids.bvecs
        return (imgs,
                jsons,
                bvals,
                bvecs)
