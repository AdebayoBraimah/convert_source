# -*- coding: utf-8 -*-
"""Batch conversion wrapper and its associated classes and functions for the `convert_source` package.
"""

# TODO:
#   * [ ] Write integration test(s)
#   * [ ] Separate unit and integration test(s) into different directories
# 
#   * [-] Add file search for image files with no extensions (DICOMs)
#       * [-] Use is_valid_dicom function when walking through directories
#       * NOTE: The implementation for this would require massive additions to
#           several modules. It would actually be far easier to just rename the
#           DICOM files and add their extensions.
# 
#   * [X] Add function to write dataset_description.json file
#       * [ ] Add function to collect and construct dictionary to fill this out
# 
#   * [ ] Add function to download latest version of dcm2niix
#   * [ ] Convert lists to queues for faster runtime performance
# 
#   * [ ] Add compatibility to use Octave/MATLAB and dicm2nii for file conversion
#       * [ ] Add option to download the most recent version of dicm2nii

import os
import glob
import yaml
import pathlib
import pandas as pd

from copy import deepcopy
from shutil import copy
from datetime import datetime
from tqdm import tqdm

from typing import (
    List, 
    Dict, 
    Optional,
    Union, 
    Tuple,
    Set
)

from convert_source.cs_utils.const import (
    DEFAULT_CONFIG,
    BIDS_PARAM,
    DEFAULT_BIDS_VERSION
)

from convert_source.cs_utils.fileio import (
    Command, 
    ConversionError,
    File,
    NiiFile,
    LogFile,
    TmpDir
)

from convert_source.cs_utils.utils import (
    BIDSimg,
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
    dict_multi_update,
    add_to_zeropadded,
    list_dir_files
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

from convert_source.cs_utils.database import (
    create_db,
    update_table_row,
    export_bids_scans_dataframe,
    query_db
)

# Define function(s)
def batch_proc(study_img_dir: str,
               out_dir: str,
               config_file: str,
               path_envs: List[str] = [],
               gzip: bool = True,
               append_dwi_info: bool = True,
               zero_pad: int = 2,
               cprss_lvl: int = 6,
               verbose: bool = False,
               write_participants: bool = False,
               write_subs_scans: bool = False,
               env: Optional[Dict] = {},
               dryrun: bool = False
               ) -> Tuple[List[str]]:
    """Batch processes a study's source image data provided a configuration, the parent directory of the study's imaging data,
    and an output directory to place the BIDS NIFTI data.

    Usage example:
        >>> subs_bids_data = batch_proc(config_file,
        ...                             study_img_dir,
        ...                             out_dir)
        ...

    Arguments:
        study_img_dir: Path to study image parent directory that contains all the subjects' source image data.
        out_dir: Output directory.
        config_file: Configuration file.
        path_envs: List of directory paths to append to the system's ``PATH`` variable.
        gzip: Gzip output NIFTI files.
        append_dwi_info: RECOMMENDED: Appends DWI acquisition information (unique non-zero b-values, and TE, in msec.) to BIDS acquisition filename.
        zero_pad: Number of zeroes to pad the run number up to (zero_pad=2 is ``01``).
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest.
        verbose: Enable verbose output.
        write_participants: If true, writes the ``participants`` TSV and JSON files to the output BIDS directory.
        write_subs_scans: If true, writes each subject's ``scan.tsv`` to their subject directory.
        env: Path environment dictionary.
        dryrun: Perform dryrun (creates the command, but does not execute it).

    Returns:
        Tuple of lists that consists of: 
            * List of NIFTI images.
            * Corresponding list of JSON sidecars.
            * Corresponding list of bval files.
            * Corresponding list of bvec files.
    """
    study_img_dir: str = os.path.abspath(study_img_dir)
    
    # Check dependencies
    dcm2niix_cmd: Command = Command("dcm2niix")
    dcm2niix_cmd.check_dependency(path_envs=path_envs)

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

    _log: str = os.path.join(misc_dir,f"convert_source_{dt_string}.log")
    log: LogFile = log_file(log=_log, verbose=verbose)

    # Create file database
    database: str = os.path.join(misc_dir,'convert_source.db')
    
    if os.path.exists(database):
        log.info("Source image file database already exists")
    else:
        database: str = create_db(database=database)
        log.info("Created source image file database")

    # Write bidsignore
    ignore_file: str = os.path.join(out_dir,'.bidsignore')

    if os.path.exists(ignore_file):
        log.info(".bidsignore file already exists")
    else:
        _ = bids_ignore(out_dir=out_dir)
        log.info("Wrote .bidsignore file")

    # Write README file
    readme_file: str = os.path.join(out_dir,'README')

    if os.path.exists(readme_file):
        log.info("README file already exists in BIDS directory")
    else:
        _ = add_readme(out_dir=out_dir)
        log.info("Added README file to BIDS directory")

    log.info("Read configuration file")

    [search_dict,
     bids_search,
     bids_map,
     meta_dict,
     exclusion_list] = read_config(config_file=config_file,
                                   verbose=verbose)

    # Dataset description file
    dataset_description: str = os.path.join(out_dir,'dataset_description.json')

    if os.path.exists(dataset_description):
        log.info("Dataset description JSON file already exists in BIDS directory")
    else:
        _ = add_dataset_description(out_dir=out_dir)
        log.info("Added dataset description JSON file to BIDS directory")
    
    # Check BIDS search and map dictionaries
    if comp_dict(d1=bids_search,d2=bids_map):
        pass
    
    log.info("Collected subject imaging data")

    subs_data: List[SubDataInfo] = collect_info(parent_dir=study_img_dir,
                                                database=database,
                                                exclusion_list=exclusion_list,
                                                log=log)

    bids_imgs: List = []
    bids_jsons: List = []
    bids_bvals: List = []
    bids_bvecs: List = []
       
    for sub_data in tqdm(subs_data,
                         desc="Processing source data files",
                         position=0,
                         leave=True):
        log.info(f"\n\n Processing: {sub_data.data} \n")

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
                                        
        try:
            [imgs,
            jsons,
            bvals,
            bvecs] = data_to_bids(sub_data=sub_data,
                                bids_name_dict=bids_name_dict,
                                out_dir=out_dir,
                                database=database,
                                modality_type=modality_type,
                                modality_label=modality_label,
                                task=task,
                                meta_dict=meta_com_dict,
                                mod_dict=meta_scan_dict,
                                log=log,
                                gzip=gzip,
                                append_dwi_info=append_dwi_info,
                                zero_pad=zero_pad,
                                cprss_lvl=cprss_lvl,
                                verbose=verbose,
                                env=env,
                                dryrun=dryrun)
        except AttributeError:
            imgs = [""]
            jsons = [""]
            bvals = [""]
            bvecs = [""]
        
        bids_imgs.extend(imgs)
        bids_jsons.extend(jsons)
        bids_bvals.extend(bvals)
        bids_bvecs.extend(bvecs)

    for i in tqdm(reversed(range(0,len(bids_imgs))),
                  desc="Verifying converted BIDS NIFTI files",
                  position=0,
                  leave=True):
        if (bids_imgs[i] == "") and (bids_jsons[i] == "") and (bids_bvals[i] == "") and (bids_bvecs[i] == ""):
            bids_imgs.pop(i)
            bids_jsons.pop(i)
            bids_bvals.pop(i)
            bids_bvecs.pop(i)

    unknown_bids_dir: str = os.path.join(out_dir,"unknown")

    if os.path.exists(unknown_bids_dir):
        log.info("Wrote unknown BIDS subject NIFTIs to file")
        output_file: str = os.path.join(unknown_bids_dir,"unknown_file_map")

        _ = write_unknown_to_file(bids_unknown_dir=unknown_bids_dir,
                                out_name=output_file,
                                yaml_file=True,
                                json_file=True)

    # Add option for writing participants and scans TSV
    if write_participants:
        log.info("Wrote participants.tsv to file")
        [_,_] = create_participant_tsv(out_dir=out_dir)

    if write_subs_scans:
        log.info("Wrote each subject's scans.tsv to file")
        subs_list: List[str] = list_dir_files(pathname=out_dir,
                                            pattern="sub-*",
                                            file_name_only=True)
        subs_list: List[str] = [ x.replace('sub-','') for x in subs_list ]

        for sub in tqdm(subs_list,
                        desc="Writing scan files",
                        position=0,
                        leave=True):
            try:
                ses_list: List[str] = list_dir_files(pathname=os.path.join(out_dir,f"sub-{sub}"),
                                                pattern="ses-*",
                                                file_name_only=True)
                ses_list: List[str] = [ x.replace('ses-','') for x in ses_list ]
            except FileNotFoundError:
                ses_list: List = []
            
            if len(ses_list) == 0:
                df: pd.DataFrame = export_bids_scans_dataframe(database=database,
                                                            sub_id=sub,
                                                            search_dict=search_dict,
                                                            gzipped=gzip)
                
                if len(df) == 0:
                    continue
                else:
                    out_name: str = os.path.join(out_dir,f'sub-{sub}',f'sub-{sub}' + '_scans.tsv')
                    
                    if os.path.exists(out_name):
                        os.remove(out_name)
                        
                    df.to_csv(out_name,
                            sep='\t',
                            na_rep='n/a',
                            index=False,
                            mode="a",
                            encoding='utf-8')
            else:
                for ses in ses_list:
                    df: pd.DataFrame = export_bids_scans_dataframe(database=database,
                                                            sub_id=sub,
                                                            search_dict=search_dict,
                                                            gzipped=gzip,
                                                            ses_id=ses)
                    if len(df) == 0:
                        continue
                    else:
                        out_name: str = os.path.join(out_dir,f'sub-{sub}',f'ses-{ses}',f'sub-{sub}_ses-{ses}' + '_scans.tsv')
                        
                        if os.path.exists(out_name):
                            os.remove(out_name)
                            
                        df.to_csv(out_name,
                                sep='\t',
                                na_rep='n/a',
                                index=False,
                                mode="a",
                                encoding='utf-8')

    return (bids_imgs,
            bids_jsons,
            bids_bvals,
            bids_bvecs)

def read_config(config_file: Optional[str] = "", 
                verbose: Optional[bool] = False
                ) -> Tuple[Dict[str,str],Dict,Dict,Dict,List[str]]:
    """Reads configuration file and creates a dictionary of search terms for 
    each modality provided that each BIDS modality is used as a key via the 
    keyword ``modality_search``. Should BIDS related parameter descriptions need 
    to be used when renaming files, the related search and mapping terms can included 
    via the keywords ``bids_search`` and ``bids_map``, respectively. If these keywords 
    are not specified, then empty dictionaries are returned. Should exclusions be provided 
    (via the key ``exclude``) then an exclusion list is created. Should this not be provided, 
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
    """
    class ConfigFileReadError(Exception):
        pass

    if config_file:
        config_file: str = os.path.abspath(config_file)
    else:
        config_file: str = DEFAULT_CONFIG

    with open(config_file) as file:
        data_map: Dict[str,str] = yaml.safe_load(file)
        if verbose:
            print("\n Initialized parameters from configuration file")
    
    # Required modality search terms
    if any("modality_search" in data_map for element in data_map):
        if verbose:
            print("\n Categorizing search terms")
        search_dict: Dict[str,str] = data_map["modality_search"]
    else:
        if verbose:
            print("\n Heuristic search terms required. Exiting...")
        raise ConfigFileReadError("Heuristic search terms required. Exiting...")
    
    # BIDS search terms
    if any("bids_search" in data_map for element in data_map):
        if verbose:
            print("\n Including BIDS related search term settings")
        bids_search: Dict[str,str] = data_map["bids_search"]
    else:
        if verbose:
            print("\n No BIDS related search term settings")
        meta_dict: Dict = dict()
    
    # BIDS mapping terms
    if any("bids_map" in data_map for element in data_map):
        if verbose:
            print("\n Corresponding BIDS mapping settings")
        bids_map: Dict[str,str] = data_map["bids_map"]
    else:
        if verbose:
            print("\n No BIDS mapping settings")
        meta_dict: Dict = dict()
    
    # Metadata terms
    if any("metadata" in data_map for element in data_map):
        if verbose:
            print("\n Including additional settings for metadata")
        meta_dict: Dict[str,Union[str,int]] = data_map["metadata"]
    else:
        if verbose:
            print("\n No metadata settings")
        meta_dict: Dict = dict()
    
    # Exclusion terms/terms to ignore
    if any("exclude" in data_map for element in data_map):
        if verbose:
            print("\n Exclusion option implemented")
        exclusion_list: List[str] = data_map["exclude"]
    else:
        if verbose:
            print("\n Exclusion option not implemented")
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
            task: Optional[str] = "",
            mod_found: bool = False
           ) -> Tuple[Dict[str,str],str,str,str]:
    """Performs identification of descriptive BIDS information relevant for file naming, provided
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
        mod_found: Boolean value that indicates if the (BIDS) modality or matching modality has been identified/found.

    Returns:
        Tuple that consists of:
            * Nested dictionary of BIDS descriptive naming related terms.
            * Modality type.
            * Modality label.
            * Task label.
    """
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
    
    if mod_found and modality_type:
        modality_type: str = modality_type
        modality_label: str = modality_label
        task: str = task
        bids_name_dict: Dict = search_bids(s=s,
                                           bids_search=bids_search,
                                           bids_map=bids_map,
                                           modality_type=modality_type,
                                           modality_label=modality_label,
                                           bids_name_dict=bids_name_dict)
    else:
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
                             task=task,
                             mod_found=True)
    
    return (bids_name_dict,
            modality_type,
            modality_label,
            task)

def _gather_bids_name_args(bids_name_dict: Dict,
                           modality_type: str,
                           param: str
                          ) -> Union[str,bool]:
    """Helper function that gathers BIDS naming description arguments for the ``construct_bids_name`` function. In the case that ``fmap`` is passed as the 
    ``modality_type`` argument, then the ``param`` argument must be either: ``mag2``, ``case1``, ``case2``, ``case3``, or ``case4``.
    
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
        String from the BIDS name description dictionary if it exists, or an empty string otherwise. In the case of ``fmap``, then a boolean value is returned.
    """
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
        try:
            return bids_name_dict[modality_type].get(param,'')
        except KeyError:
            return ''

def _get_bids_name_args(bids_name_dict: Dict,
                        modality_type: str
                        ) -> Tuple[str,bool]:
    """Helper function that wraps the funciton ``_gather_bids_name_args``.
    
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
    """
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
    """Creates a BIDS compliant filename given a BIDS name description dictionary, and the modality type.

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
    """
    
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

    # Set multiple run names
    run1: str = str(run)
    run2: str = add_to_zeropadded(run,1)
    run3: str = add_to_zeropadded(run,2)
    run4: str = add_to_zeropadded(run,3)

    f_name1: str = f_name + f"_run-{run1}"
    f_name2: str = f_name + f"_run-{run2}"
    f_name3: str = f_name + f"_run-{run3}"
    f_name4: str = f_name + f"_run-{run4}"

    if echo and ('echo' in bids_keys):
        f_name1 += f"_echo-{echo}"
        f_name2 += f"_echo-{echo}"
        f_name3 += f"_echo-{echo}"
        f_name4 += f"_echo-{echo}"
    
    if modality_type.lower() == 'fmap':
        if case1 and mag2:
            f_name1: str = f_name1 + "_phasediff"
            f_name2: str = f_name1 + "_magnitude1"
            f_name3: str = f_name1 + "_magnitude2"
            return (f_name1,
                   f_name2,
                   f_name3,
                   "")
        elif case1:
            f_name1: str = f_name1 + "_phasediff"
            f_name2: str = f_name1 + "_magnitude1"
            return (f_name1,
                   f_name2,
                   "",
                   "")
        elif case2:
            f_name1: str = f_name1 + "_phase1"
            f_name2: str = f_name1 + "_phase2"
            f_name3: str = f_name1 + "_magnitude1"
            f_name4: str = f_name1 + "_magnitude2"
            return (f_name1,
                   f_name2,
                   f_name3,
                   f_name4)
        elif case3:
            f_name1: str = f_name1 + "_magnitude"
            f_name2: str = f_name1 + "_fieldmap"
            return (f_name1,
                   f_name2,
                   "",
                   "")
        elif case4:
            modality_label = bids_name_dict[modality_type]['modality_label']
            f_name1 += f"_{modality_label}"
            f_name2 += f"_{modality_label}"
            f_name3 += f"_{modality_label}"
            f_name4 += f"_{modality_label}"
            return (f_name1,
                    f_name2,
                    f_name3,
                    f_name4)
    else:
        modality_label = bids_name_dict[modality_type]['modality_label']
        f_name1 += f"_{modality_label}"
        f_name2 += f"_{modality_label}"
        f_name3 += f"_{modality_label}"
        f_name4 += f"_{modality_label}"
        return (f_name1,
                f_name2,
                f_name3,
                f_name4)

def source_to_bids(sub_data: SubDataInfo,
                   bids_name_dict: Dict,
                   out_dir: str,
                   database: str,
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
    """Converts source data to BIDS raw data.
    
    Usage example:
        >>> [imgs, jsons, bvals, bvecs] = source_to_bids(sub_obj,
        ...                                              bids_name_dict,
        ...                                              output_dir,
        ...                                              database,
        ...                                              'anat',
        ...                                              'T1w')
        ...

    Arguments:
        sub_data: Subject data information object.
        bids_name_dict: BIDS name dictionary.
        out_dir: Output directory.
        database: Input database filename to be queried and updated.
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
    """
    sub: Union[int,str] = sub_data.sub
    ses: Union[int,str] = sub_data.ses
    data: str = sub_data.data
    
    sub_dir: str = os.path.join(out_dir,"sub-" + sub)
    sub_tmp: str = sub_dir
    
    if ses:
        sub_dir: str = os.path.join(sub_dir,"ses-" + ses)

    # Gather BIDS name description args
    [_task, 
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

    if _task == task:
        pass
    elif _task:
        task: str = _task

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

                        metadata: Dict = dict_multi_update(dictionary=None, **meta_dict)
                        metadata: Dict = dict_multi_update(dictionary=metadata, **param_dict)
                        metadata: Dict = dict_multi_update(dictionary=metadata, **mod_dict)

                        bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                              json_dict=json_dict)

                        img_data.jsons[i] = write_json(json_file=img_data.jsons[i],
                                                            dictionary=bids_dict)

                        if (modality_type.lower() == 'dwi' or modality_label.lower() == 'dwi') and append_dwi_info:
                            bvals: List[int] = get_bvals(img_data.bvals[i])
                            echo_time: Union[int,str] = bids_dict.get("EchoTime",'')
                            _label: str = ""
                            for bval in bvals:
                                _label += f"b{bval}"
                            if int(bvals[0]) == 0:
                                modality_label: str = "sbref"
                            if echo_time:
                                echo_time: float = float(echo_time) * 1000
                                _label += f"TE{int(echo_time)}"
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
                # by calling nifti_to_bids if that is the case.
                if img_data.bvals[0] and img_data.bvecs[0] and not modality_type:
                    modality_type = 'dwi'
                    modality_label = 'dwi'
                    sub_data.data = img_data.imgs[0]
                    [imgs,
                    jsons,
                    bvals,
                    bvecs] = nifti_to_bids(sub_data=sub_data,
                                           bids_name_dict=bids_name_dict,
                                           out_dir=out_dir,
                                           modality_type=modality_type,
                                           modality_label=modality_label,
                                           task=task,
                                           meta_dict=meta_dict,
                                           mod_dict=mod_dict,
                                           gzip=gzip,
                                           append_dwi_info=append_dwi_info,
                                           zero_pad=zero_pad,
                                           cprss_lvl=cprss_lvl)
                    tmp.rm_tmp_dir()
                    return (imgs,
                            jsons,
                            bvals,
                            bvecs)

                elif len(img_data.imgs) >= 2 and not modality_type:
                    modality_type = 'fmap'
                    modality_label = 'fmap'
                    sub_data.data = img_data.imgs[0]
                    [imgs,
                    jsons,
                    bvals,
                    bvecs] = nifti_to_bids(sub_data=sub_data,
                                           bids_name_dict=bids_name_dict,
                                           out_dir=out_dir,
                                           modality_type=modality_type,
                                           modality_label=modality_label,
                                           task=task,
                                           meta_dict=meta_dict,
                                           mod_dict=mod_dict,
                                           gzip=gzip,
                                           append_dwi_info=append_dwi_info,
                                           zero_pad=zero_pad,
                                           cprss_lvl=cprss_lvl)
                    tmp.rm_tmp_dir()
                    return (imgs,
                            jsons,
                            bvals,
                            bvecs)

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

                # Update database
                database: str = update_table_row(database=database,
                                                prim_key=sub_data.file_id,
                                                table_name='bids_name',
                                                value=bids_names[0])
                
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

                # Update database
                database: str = update_table_row(database=database,
                                                prim_key=sub_data.file_id,
                                                table_name='bids_name',
                                                value="NIFTI FILE CONVERSION FAILED")
                return [""],[""],[""],[""]

def nifti_to_bids(sub_data: SubDataInfo,
                  bids_name_dict: Dict,
                  out_dir: str,
                  database: str,
                  modality_type: Optional[str] = "",
                  modality_label: Optional[str] = "",
                  task: Optional[str] = "",
                  meta_dict: Optional[Dict] = {},
                  mod_dict: Optional[Dict] = {},
                  gzip: bool = True,
                  append_dwi_info: bool = True,
                  zero_pad: int = 2,
                  cprss_lvl: int = 6
                  ) -> Tuple[List[str],List[str],List[str],List[str]]:
    """Converts existing NIFTI data to BIDS raw data.
    
    Usage example:
        >>> [imgs, jsons, bvals, bvecs] = nifti_to_bids(sub_obj,
        ...                                             bids_name_dict,
        ...                                             output_dir,
        ...                                             'anat',
        ...                                             'T1w')
        ...

    Arguments:
        sub_data: Subject data information object.
        bids_name_dict: BIDS name dictionary.
        out_dir: Output directory.
        database: Input database filename to be queried and updated.
        modality_type: Modality type (BIDS label e.g. 'anat', 'func', etc).
        modality_label: Modality label (BIDS label  e.g. 'T1w', 'bold', etc).
        task: Task label (BIDS filename task label, e.g. 'rest', 'nback', etc.)
        meta_dict: BIDS common metadata dictoinary.
        mod_dict: Modality specific metadata dictionary.
        gzip: Gzip output NIFTI files.
        append_dwi_info: Appends DWI acquisition information (unique non-zero b-values, and TE, in msec.) to BIDS acquisition filename.
        zero_pad: Number of zeroes to pad the run number up to (zero_pad=2 is '01').
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest.

    Returns:
        Tuple of lists that contains:
            * List of image data file(s). Empty string is returned if this file does not exist.
            * List of corresponding JSON (sidecar) file(s). Empty string is returned if this file does not exist.
            * List of corresponding FSL-style bval file(s). Empty string is returned if this file does not exist.
            * List of corresponding FSL-style bvec file(s). Empty string is returned if this file does not exist.
    """
    sub: Union[int,str] = sub_data.sub
    ses: Union[int,str] = sub_data.ses
    data: str = sub_data.data
    
    sub_dir: str = os.path.join(out_dir,"sub-" + sub)
    sub_tmp: str = sub_dir
    
    if ses:
        sub_dir: str = os.path.join(sub_dir,"ses-" + ses)
    
    # Gather BIDS name description args
    [_task, 
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
    
    if _task == task:
        pass
    elif _task:
        task: str = _task

    # Use TmpDir and NiiFile class context managers
    with TmpDir(tmp_dir=sub_tmp, use_cwd=False) as tmp:
        tmp.mk_tmp_dir()
        with NiiFile(data) as n:
            [path, basename, ext] = n.file_parts()
            img_files: List[str] = glob.glob(os.path.join(path,basename + "*" + ext))
            json_files: List[str] = glob.glob(os.path.join(path,basename + "*.json*"))
            bval_files: List[str] = glob.glob(os.path.join(path,basename + "*.bval*"))
            bvec_files: List[str] = glob.glob(os.path.join(path,basename + "*.bvec*"))

            for i in range(0,len(img_files)):
                if img_files[i]:
                    copy(img_files[i],tmp.tmp_dir)
                
                try:
                    if json_files[i]:
                        copy(json_files[i],tmp.tmp_dir)
                except IndexError:
                    pass
                
                try:
                    if bval_files[i]:
                        copy(bval_files[i],tmp.tmp_dir)
                except IndexError:
                    pass
                
                try:
                    if bvec_files[i]:
                        copy(bvec_files[i],tmp.tmp_dir)
                except IndexError:
                    pass
            
            img_data: BIDSimg = BIDSimg(work_dir=tmp.tmp_dir)

            # NOTE: This assumes that there is ONLY one set of bval, and bvec files,
            #   while several, or multiple NIFTI images or JSON files may exist.

            for i in range(0,len(img_data.imgs)):
                if img_data.jsons[i]:
                    json_dict: Dict = read_json(json_file=img_data.jsons[i])

                    param_dict: Dict = get_data_params(file=data,
                                                    json_file=img_data.jsons[i])

                    metadata: Dict = dict_multi_update(dictionary=None, **meta_dict)
                    metadata: Dict = dict_multi_update(dictionary=metadata, **param_dict)
                    metadata: Dict = dict_multi_update(dictionary=metadata, **mod_dict)

                    bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                        json_dict=json_dict)

                    img_data.jsons[i] = write_json(json_file=img_data.jsons[i],
                                                    dictionary=bids_dict)
                elif (not img_data.jsons[i]) and (i == 0):
                    json_dict: Dict = read_json(json_file="")

                    param_dict: Dict = get_data_params(file=data,
                                                    json_file=img_data.jsons[i])

                    metadata: Dict = dict_multi_update(dictionary=None, **meta_dict)
                    metadata: Dict = dict_multi_update(dictionary=metadata, **param_dict)
                    metadata: Dict = dict_multi_update(dictionary=metadata, **mod_dict)
                    
                    bids_dict: Dict = construct_bids_dict(meta_dict=metadata,
                                                        json_dict=json_dict)

                    img_data.jsons[i] = write_json(json_file=os.path.join(tmp.tmp_dir,'tmp.json'),
                                                    dictionary=bids_dict)

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
            
            if modality_type.lower() == 'dwi' or modality_type.lower() == 'func' :
                num_frames = get_num_frames(img_data.imgs[0])
                if num_frames == 1:
                    modality_label: str = "sbref"

            if (modality_type.lower() == 'dwi' or modality_label.lower() == 'dwi') and append_dwi_info:
                bvals: List[int] = get_bvals(img_data.bvals[0])
                echo_time: Union[int,str] = bids_dict.get("EchoTime",'')
                _label: str = ""
                for bval in bvals:
                    _label += f"b{bval}"
                if int(bvals[0]) == 0:
                    modality_label: str = "sbref"
                if echo_time:
                    echo_time: float = float(echo_time) * 1000
                    _label += f"TE{int(echo_time)}"
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

            # Update database
            database: str = update_table_row(database=database,
                                            prim_key=sub_data.file_id,
                                            table_name='bids_name',
                                            value=bids_names[0])
            
            for i in range(0,len(img_data.imgs)):
                out_name: str = os.path.join(out_data_dir,bids_names[i])

                out_nii: str = out_name + ext
                out_json: str = out_name + ".json"
                out_bval: str = out_name + ".bval"
                out_bvec: str = out_name + ".bvec"

                out_nii = copy(img_data.imgs[i],out_nii)

                if img_data.jsons[i]:
                    out_json = copy(img_data.jsons[i],out_json)
                
                if gzip and ('.nii.gz' in out_nii):
                    out_tmp: str = gunzip_file(file=out_nii,
                                            native=True)
                    out_nii = gzip_file(file=out_tmp,
                                        cprss_lvl=cprss_lvl,
                                        native=True)
                elif (not gzip) and ('.nii.gz' in out_nii):
                    out_nii = gunzip_file(file=out_nii,
                                        native=True)
                elif gzip and ('.nii' in out_nii):
                    out_nii = gzip_file(file=out_nii,
                                        cprss_lvl=cprss_lvl,
                                        native=True)
                
                imgs.append(out_nii)
                jsons.append(out_json)
                
                if img_data.bvals[i] and img_data.bvecs[i]:
                    out_bval = copy(img_data.bvals[i],out_bval)
                    out_bvec = copy(img_data.bvecs[i],out_bvec)
                    bvals.append(out_bval)
                    bvecs.append(out_bvec)
                else:
                    out_bval: str = ""
                    out_bvec: str = ""
                    bvals.append("")
                    bvecs.append("")
        # Clean-up
        tmp.rm_tmp_dir()

        return (imgs,
                jsons,
                bvals,
                bvecs)

def data_to_bids(sub_data: SubDataInfo,
                 bids_name_dict: Dict,
                 out_dir: str,
                 database: str,
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
    """Converts source data to BIDS compliant data. This functions also
    renames already existing NIFTI data so that it can be BIDS compliant.
    
    Usage example:
        >>> [imgs, jsons, bvals, bvecs] = data_to_bids(sub_obj,
        ...                                            bids_name_dict,
        ...                                            output_dir,
        ...                                            database,
        ...                                            'anat',
        ...                                            'T1w')
        ...

    Arguments:
        sub_data: Subject data information object.
        bids_name_dict: BIDS name dictionary.
        out_dir: Output directory.
        database: Input database filename to be queried and updated.
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
    """
    if ('.dcm' in sub_data.data.lower()) or ('.par' in sub_data.data.lower()):
        [imgs,
         jsons,
         bvals,
         bvecs] = source_to_bids(sub_data=sub_data,
                                 bids_name_dict=bids_name_dict,
                                 out_dir=out_dir,
                                 database=database,
                                 modality_type=modality_type,
                                 modality_label=modality_label,
                                 task=task,
                                 meta_dict=meta_dict,
                                 mod_dict=mod_dict,
                                 gzip=gzip,
                                 append_dwi_info=append_dwi_info,
                                 zero_pad=zero_pad,
                                 cprss_lvl=cprss_lvl,
                                 verbose=verbose,
                                 log=log,
                                 env=env,
                                 dryrun=dryrun)
        return (imgs,
                jsons,
                bvals,
                bvecs)
    elif '.nii' in sub_data.data.lower():
        [imgs,
         jsons,
         bvals,
         bvecs] = nifti_to_bids(sub_data=sub_data,
                                bids_name_dict=bids_name_dict,
                                out_dir=out_dir,
                                database=database,
                                modality_type=modality_type,
                                modality_label=modality_label,
                                task=task,
                                meta_dict=meta_dict,
                                mod_dict=mod_dict,
                                gzip=gzip,
                                append_dwi_info=append_dwi_info,
                                zero_pad=zero_pad,
                                cprss_lvl=cprss_lvl)
        return (imgs,
                jsons,
                bvals,
                bvecs)
    else:
        # Update database
        database: str = update_table_row(database=database,
                                        prim_key=sub_data.file_id,
                                        table_name='bids_name',
                                        value="NIFTI FILE CONVERSION FAILED")
        return [""],[""],[""],[""]


def bids_ignore(out_dir: str) -> str:
    """Writes ``.bidsignore`` file. This file functions 
    similarly to the '.gitignore' file.

    Usage example:
        >>> ignore = bids_ignore(out_dir)
        
    Arguments:
        out_dir: Output directory to place the file.

    Returns:
        String of the file path to the ``.bidsignore`` file.
    """
    if os.path.exists(out_dir):
        out_dir: str = os.path.abspath(out_dir)
    else:
        os.makedirs(out_dir)
        out_dir: str = os.path.abspath(out_dir)
    
    new_file: str = os.path.join(out_dir,'.bidsignore')

    # Write to file using File class context manager
    with File(new_file) as f:
        f.write_txt(".misc/* \n")
        f.write_txt("unknown/* \n")
    return new_file

def log_file(log: str,
            verbose: bool = False) -> LogFile:
    """Initializes log file object for logging purposes.

    Usage example:
        >>> logger = log(log_file)
        >>>
        >>> logger.info("Some information")
        >>> logger.warning("Some warning")
        
    Arguments:
        log: Log file name.
        verbose: Permits verbose logging to screen (stdout).

    Returns:
        LogFile object to be logged to.
    """
    from convert_source import __version__

    log: LogFile = LogFile(log_file=log, print_to_screen=verbose)

    now = datetime.now()
    dt_string = now.strftime("%A %B %d, %Y %H:%M:%S")
    dcm2niix_version: str = get_dcm2niix_version()

    log.info(f"convert_source start: {dt_string}")
    log.info(f"convert_source v{__version__}")
    log.info(f"dcm2niix {dcm2niix_version}")
    return log

def get_dcm2niix_version() -> str:
    """Gets the version of ``dcm2niix`` being used on the current OS. 

    This function assumes that dependency checks have already been performed, and that ``dcm2niix`` is in the system path.

    Usage example:
        >>> dcm_cmd = Command("dcm2niix)
        >>> dcm.check_dependency(
        ...         path_envs=[ '/<path>/<to>/<dcm2niix>' ])
        ...
        >>> dcm_version = get_dcm2niix_version()
        >>> dcm_version
        'v1.0.20201102'

    Returns:
        ``dcm2niix`` version used on the current OS.
    """
    dcm_ver_txt: str = os.path.join(os.getcwd(),'dcm2niix.version.txt')
    dcm_ver_err: str = os.path.join(os.getcwd(),'dcm2niix.version.err')

    dcm: Command = Command("dcm2niix")
    dcm.cmd_list.append("--version")
    dcm.run(stdout=dcm_ver_txt)

    print("\n\n Disregard 'Failed with returncode 3' message - this message arises when obtaining dcm2niix's version. \n")

    with open(dcm_ver_txt,'r') as f:
        lines = f.readlines()
        lines = [ x.strip('\n') for x in lines ]
        f.close()
    
    os.remove(dcm_ver_txt)
    os.remove(dcm_ver_err)
    return lines[1]

def write_unknown_to_file(bids_unknown_dir: str,
                        out_name: str,
                        yaml_file: bool = True,
                        json_file: bool = False
                        ) -> Tuple[List[str],str,str]:
    """Writes unknown BIDS NIFTIs to either a YAML or JSON file to later be identified and renamed to be BIDS compatible.
    If both the ``yaml_file`` and ``json_file`` options are false, an exception is raised.

    NOTE: 
        The ``out_name`` argument should only have the file name provided, and not the absolute path, as the ``bids_unknown_dir`` 
        path is pre-pended to ``out_name``.

    Usage example:
        >>> [ unknown_list, yml_file, json_file ] = write_unknown_to_file(bids_unknown_dir='<BIDS rawdata directory>/unknown',
        ...                                                               out_name='unknown',
        ...                                                               yaml_file=True,
        ...                                                               json_file=False)
        ...

    Arguments:
        bids_unknown_dir: Unknown BIDS directory that contains unknown BIDS files.
        out_name: Output file prefix (i.e. no file extension).
        yaml_file: If true, writes the output file as a YAML file.
        json_file: If true, writes the output file as a JSON file.

    Returns:
        Tuple that consists of:
            * List of unknown BIDS NIFTI files.
            * Output YAML file.
            * Output JSON file.

    Raises:
        FileNotFoundError: Error that arises if the specified unknown BIDS directory does not exist.
        NameError: Error that arises if both YAML and JSON output options are set to false.
    """
    if os.path.exists(bids_unknown_dir):
        pass
    else:
        raise FileNotFoundError("The specified unknown BIDS directory does not exist.")
    
    if (not yaml_file) and (not json_file):
        raise NameError("Both JSON and YAML options are set to false.")

    unknown_bids: List[str] = list_dir_files(pathname=bids_unknown_dir,
                                            pattern="*.nii*",
                                            file_name_only=True)

    unknown_dict: Dict = {}

    for nii_file in unknown_bids:
        tmp_dict: Dict[str,str] = {
            nii_file: 
            {
                'modality_type':'',
                'modality_label':''
            }
        }
        unknown_dict.update(tmp_dict)

    if yaml_file:
        output_yaml: str = out_name + ".yml"
        with open(output_yaml, 'w') as outfile:
            yaml.dump(unknown_dict, 
                    outfile, 
                    default_flow_style=False,
                    sort_keys=True)
    else:
        output_yaml: str = ""

    if json_file:
        output_json: str = out_name + ".json"
        output_json: str = write_json(json_file=output_json,
                                    dictionary=unknown_dict)
    else:
        output_json: str = ""
    
    return (unknown_bids, 
            output_yaml, 
            output_json)

def add_dataset_description(out_dir: str) -> str:
    """Adds the ``dataset_description.json`` (dataset description JSON) file to some BIDS data directory.
    This is essentially meant to function as a boiler plate dataset_description template.

    NOTE:
        This template was obtained from: https://bids-specification.readthedocs.io/en/v1.6.0/03-modality-agnostic-files.html#dataset-description
        Boiler plate dataset_description template.
    
    Usage example:
        >>> ds_json = add_dataset_description(out_dir='<path>/<to>/<BIDS>')

    Arguments:
        out_dir: Output BIDS directory.

    Returns:
        File path to dataset_description.json file as a string.
    """
    # TODO:
    #   * Function that constructs dictionary for dataset descrtption
    #       * Perhaps have it read in through config file.
    data: Dict[str,str] = {
        "Name":"",
        "BIDSVersion": DEFAULT_BIDS_VERSION,
        "HEDVersion":"",
        "DatasetType":"raw",
        "License":"",
        "Authors":[
            "Author 1",
            "Author 2",
            "Author 3"
        ],
        "Acknowledgements":"",
        "HowToAcknowledge":"",
        "Funding":[
            "Funding source 1",
            "Funding source 2"
        ],
        "EthicsApprovals":[
            "IRB 1",
            "IRB 2"
        ],
       "ReferencesAndLinks":[
           "Link 1",
           "Link 2",
           "Reference 1",
           "Reference 2"
       ],
       "DatasetDOI":""
    }

    output_json: str = os.path.join(out_dir,'dataset_description.json')

    output_json: str = write_json(json_file=output_json,
                                  dictionary=data)
    return output_json

def create_participant_tsv(out_dir: str) -> Tuple[str,str]:
    """Creates or appends/updates the participants TSV file (``participants.tsv``).
    If the participants TSV file does not exist at runtime, then it is created. 
    Additionally, the participant JSON file is created. 
    However once created, it is not updated (as this is intended to be maintained by the user).

    More information can be obtained from: https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#participants-file

    Usage example:
        >>> [participant_tsv,
        ...  participant_json] = create_participant_tsv(out_dir="<path>/<to>/<BIDS>/<directory>")

    Arguments:
        out_dir: BIDS output directory.

    Returns:
        Tuple of strings that consist of:
            * Absolute file path to the participants TSV file (``participants.tsv``)
            * Absolute file path to the participants JSON file (``participants.json``)
    """
    participant_tsv: str = os.path.join(out_dir,'participants.tsv')
    participant_json: str = os.path.join(out_dir,'participants.json')

    if os.path.exists(participant_json):
        pass
    else:
        data: Dict[str,str] = {
            "age": {
                "Description": "age of participant",
                "Units": "years"
            },
            "sex": {
                "Description": "sex of the participant as reported by the participant",
                "Levels": {
                    "F": "female",
                    "M": "male"
                }
            },
            "handedness": {
                "Description": "handedness of the participant as reported by the participant",
                "Levels": {
                    "A": "ambidextrous",
                    "L": "left",
                    "R": "right"
                }
            },
            "group": {
                "Description": "experimental group the participant belonged to",
                "Levels": {
                    "control": "Control group",
                    "patient": "Patient group"
                }
            }
        }
        
        participant_json: str = write_json(json_file=participant_json,
                                        dictionary=data)
        
    if os.path.exists(participant_tsv):
        df_old: pd.DataFrame = pd.read_csv(participant_tsv, sep='\t')
        keys: List[str] = list(df_old.columns)

        subs_set: Set[str] = set(list_dir_files(pathname=out_dir,
                                                pattern="sub-*",
                                                file_name_only=True))
        tmp_set: Set[str] = set(list(df_old['participant_id']))
        tmp_list: List[str] = list(subs_set.difference(tmp_set))

        df_tmp: pd.DataFrame = pd.DataFrame(columns=keys)
        df_tmp['participant_id'] = tmp_list
        df_new: pd.DataFrame = pd.concat([df_old,df_tmp],
                                        axis=0)
        df_new: pd.DataFrame = df_new.reset_index()
        df_new: pd.DataFrame = df_new.drop(columns=['index'])
        df_new.sort_values(by='participant_id',
                            axis=0,
                            inplace=True)
        df_new.to_csv(participant_tsv,
                        sep='\t',
                        na_rep='n/a',
                        index=False,
                        mode='w',
                        encoding='utf-8')
        return participant_tsv, participant_json
    else:
        subs_list: List[str] = list_dir_files(pathname=out_dir,
                                            pattern="sub-*",
                                            file_name_only=True)
        df: pd.DataFrame = pd.DataFrame(columns=[
                                        'participant_id',
                                        'age',
                                        'sex',
                                        'handedness',
                                        'group'])
        df['participant_id'] = subs_list
        df.to_csv(participant_tsv,
                    sep='\t',
                    na_rep='n/a',
                    index=False,
                    mode="w",
                    encoding='utf-8')
        return participant_tsv, participant_json

def read_unknown_subs(mapfile: str,
                      config: Optional[str] = "",
                      cprss_lvl: int = 6,
                      verbose: bool = False
                      ) -> str:
    """Reads the input JSON or YAML mapfile for unknown BIDS NIFTI files.

    NOTE:
        Use of this functions requires that the function ``batch_proc`` has already been run.

    Usage example:
        >>> subs_bids_data = read_unknown_subs(mapfile)

    Arguments:
        mapfile: JSON or YAML mapfile that specifies the ``modality_type`` and ``modality_label``.
        config: Configuration file with search terms.
        cprss_lvl: Compression level [1 - 9] - 1 is fastest, 9 is smallest.
        verbose: Enable verbose output.

    Returns:
        Tuple of lists that consists of: 
            * List of NIFTI images.
            * Corresponding list of JSON sidecars.
            * Corresponding list of bval files.
            * Corresponding list of bvec files.
    """
    mapfile: str = os.path.abspath(mapfile)

    out_dir: str = os.path.join(str(pathlib.Path(os.path.abspath(mapfile)).parents[1]))
    unknown_dir: str = os.path.join(str(pathlib.Path(os.path.abspath(mapfile)).parents[0]))
    misc_dir: str = os.path.join(str(pathlib.Path(os.path.abspath(mapfile)).parents[1]),'.misc')

    now = datetime.now()
    dt_string: str = str(now.strftime("%m_%d_%Y_%H_%M"))

    _log: str = os.path.join(misc_dir,f"convert_source_{dt_string}.log")
    log: LogFile = log_file(log=_log, verbose=verbose)

    log.log("Accessed database.")
    database: str = os.path.join(misc_dir,'convert_source.db')

    if config:
        pass
    else:
        config: str = DEFAULT_CONFIG

    if ('.yml' in mapfile) or ('.yaml' in mapfile):
        with open(mapfile) as f:
            data: Dict[str,str] = yaml.safe_load(f)
            f.close()
    elif '.json' in mapfile:
        data: Dict[str,str] = read_json(json_file=mapfile)

    bids_imgs: List = []
    bids_jsons: List = []
    bids_bvals: List = []
    bids_bvecs: List = []

    for key,items in data.items():
        modality_type: str = items.get('modality_type','')
        modality_label: str = items.get('modality_label','')

        if modality_type and modality_label:

            if '.nii.gz' in key:
                ext: str = '.nii.gz'
                gzip: bool = True
            else:
                ext: str = '.nii'
                gzip: bool = False
            
            if os.path.exists(os.path.join(unknown_dir,key)):
                log.log(f"Processing: {key}")
            else:
                log.log(f"File not found: {key}.")
                continue

            sql_val: str = key.replace(ext,'')

            file_id: str = query_db(database=database, table='bids_name', prim_key='bids_name', column='file_id', value=sql_val)
            sub_id: str = query_db(database=database, table='sub_id', prim_key='file_id', value=file_id)
            ses_id: str = query_db(database=database, table='ses_id', prim_key='file_id', value=file_id)

            [search_dict,_,_,_,_] = read_config(config_file=config,verbose=verbose)

            sub_data: SubDataInfo = SubDataInfo(sub=sub_id,
                                                ses=ses_id,
                                                data=os.path.join(unknown_dir,key),
                                                file_id=file_id)
            data: str = sub_data.data
            bids_name_dict: Dict = deepcopy(BIDS_PARAM)
            bids_name_dict['info']['sub'] = sub_data.sub

            if sub_data.ses:
                bids_name_dict['info']['ses'] = sub_data.ses
            
            [bids_name_dict, 
            modality_type, 
            modality_label, 
            _] = bids_id(s=data,
                         search_dict=search_dict,
                         modality_type=modality_type,
                         modality_label=modality_label,
                         bids_name_dict=bids_name_dict,
                         mod_found=True)

            [imgs,
            jsons,
            bvals,
            bvecs] = nifti_to_bids(sub_data=sub_data,
                                   bids_name_dict=bids_name_dict,
                                   out_dir=out_dir,
                                   database=database,
                                   modality_type=modality_type,
                                   modality_label=modality_label,
                                   cprss_lvl=cprss_lvl,
                                   gzip=gzip)

            log.log(f"Converted: {key} -> {imgs[0]}")

            bids_imgs.extend(imgs)
            bids_jsons.extend(jsons)
            bids_bvals.extend(bvals)
            bids_bvecs.extend(bvecs)

    return (imgs,
            jsons,
            bvals,
            bvecs)

def add_readme(out_dir: str) -> str:
    """Adds a BIDS README file to some output BIDS directory.

    NOTE: 
        README template obtained from: https://github.com/bids-standard/bids-starter-kit/tree/master/templates

    Usage example:
        >>> readme_file = add_readme(out_dir='<path>/<to>/<BIDS>/<directory>')

    Arguments:
        out_dir: BIDS output directory for the README file.

    Returns:
        Absolute file path to README file.
    """
    read_me_txt: str = """# README

The README is usually the starting point for researchers using your data
and serves as a guidepost for users of your data. A clear and informative
README makes your data much more usable.

In general you can include information in the README that is not captured by some other
files in the BIDS dataset (dataset_description.json, events.tsv, ...).

It can also be useful to also include information that might already be 
present in another file of the dataset but might be important for users to be aware of 
before preprocessing or analysing the data.

If the README gets too long you have the possibility to create a `/doc` folder
and add it to the `.bidsignore` file to make sure it is ignored by the BIDS validator.

More info here: https://neurostars.org/t/where-in-a-bids-dataset-should-i-put-notes-about-individual-mri-acqusitions/17315/3

## Details related to access to the data

- [ ] Data user agreement

If the dataset requires a data user agreement, link to the relevant information.

- [ ] Contact person

Indicate the name and contact details (email and ORCID) of the person responsible for additional information.

- [ ] Practical information to access the data

If there is any special information related to access rights or 
how to download the data make sure to include it. 
For example, if the dataset was curated using datalad, 
make sure to include the relevant section from the datalad handbook:
http://handbook.datalad.org/en/latest/basics/101-180-FAQ.html#how-can-i-help-others-get-started-with-a-shared-dataset

## Overview

- [ ] Project name (if relevant)

- [ ] Year(s) that the project ran

If no `scans.tsv` is included, this could at least cover when the data acquisition 
starter and ended. Local time of day is particularly relevant to subject state.

- [ ] Brief overview of the tasks in the experiment

A paragraph giving an overview of the experiment. This should include the 
goals or purpose and a discussion about how the experiment tries to achieve
these goals.

- [ ] Description of the contents of the dataset

An easy thing to add is the output of the bids-validator that describes what type of 
data and the number of subject one can expect to find in the dataset. 

- [ ] Independent variables

A brief discussion of condition variables (sometimes called contrasts
or independent variables) that were varied across the experiment.

- [ ] Dependent variables

A brief discussion of the response variables (sometimes called the
dependent variables) that were measured and or calculated to assess
the effects of varying the condition variables. This might also include
questionnaires administered to assess behavioral aspects of the experiment.

- [ ] Control variables

A brief discussion of the control variables --- that is what aspects 
were explicitly controlled in this experiment. The control variables might 
include subject pool, environmental conditions, set up, or other things 
that were explicitly controlled.

- [ ] Quality assessment of the data

Provide a short summary of the quality of the data ideally with descriptive statistics if relevant
and with a link to more comprehensive description (like with MRIQC) if possible.

## Methods  

### Subjects

A brief sentence about the subject pool in this experiment.

Remember that `Control` or `Patient` status should be defined in the `participants.tsv`
using a group column.

- [ ] Information about the recruitment procedure
- [ ] Subject inclusion criteria (if relevant)
- [ ] Subject exclusion criteria (if relevant)
 
### Apparatus

A summary of the equipment and environment setup for the
experiment. For example, was the experiment performed in a shielded room
with the subject seated in a fixed position.

### Initial setup

A summary of what setup was performed when a subject arrived.

### Task organization

How the tasks were organized for a session.
This is particularly important because BIDS datasets usually have task data
separated into different files.) 

- [ ] Was task order counter-balanced?
- [ ] What other activities were interspersed between tasks?  

- [ ] In what order were the tasks and other activities performed? 

### Task details

As much detail as possible about the task and the events that were recorded. 

### Additional data acquired

A brief indication of data other than the
imaging data that was acquired as part of this experiment. In addition
to data from other modalities and behavioral data, this might include
questionnaires and surveys, swabs, and clinical information. Indicate
the availability of this data.

This is especially relevant if the data are not included in a `phenotype` folder.
https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#phenotypic-and-assessment-data

### Experimental location

This should include any additional information regarding the 
the geographical location and facility that cannot be included
in the relevant json files.

### Missing data

Mention something if some participants are missing some aspects of the data.
This can take the form of a processing log and/or abnormalities about the dataset. 

Some examples:

- A brain lesion or defect only present in one participant
- Some experimental conditions missing on a given run for a participant because
  of some technical issue.
- Any noticeable feature of the data for certain participants
- Differences (even slight) in protocol for certain participants.

### Notes

Any additional information or pointers to information that
might be helpful to users of the dataset. Include qualitative information 
related to how the data acquisition went.
    """
    readme_file: str = os.path.join(out_dir,'README')

    with File(file=readme_file) as f:
        f.touch()
        f.write_txt(txt=read_me_txt)
    return readme_file
