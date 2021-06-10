# -*- coding: utf-8 -*-
"""BIDS (Brain Imaging Data Structure) related exceptions, and functions for ascertaining metadata and filenames.
"""
import os
import glob
from collections import OrderedDict
from copy import deepcopy

from typing import (
    Dict,
    List, 
    Optional,
    Union
)

from convert_source.cs_utils.utils import (
    dict_multi_update,
    SubDataInfo,
    zeropad,
    depth,
    list_in_substr
)

from convert_source.cs_utils.const import (
    BIDS_INFO,
    BIDS_ORD_ARR,
    BIDS_PARAM
)

# Define exceptions
class BIDSNameError(Exception):
    pass

class BIDSMetaDataError(Exception):
    pass

# Define function(s)
def is_camel_case(s: str,
                  bids_case: bool = True
                  ) -> bool:
    """Tests if some input string is camel case (CamelCase).

    NOTE: 
        This function is configured for BIDS use cases, in which metadata must be in camel case, with the first letter being uppercase.

    Usage example:
        >>> is_camel_case("CamelCase", bids_case=True)
        True
        >>> is_camel_case("camelcase", bids_case=True)
        False
        >>> is_camel_case("camelCase", bids_case=True)
        False
        >>> is_camel_case("camelCase", bids_case=False)
        True
        
    Arguments:
        s: Input string to test.
        bids_case: In addition to being in camel case, the string's first letter must also be
            uppercase. 

    Returns:
        Boolean.
    """
    if bids_case:
        return s != s.lower() and s != s.upper() and s[0].isupper() and "_" not in s
    else:
        return s != s.lower() and s != s.upper() and "_" not in s

def construct_bids_dict(meta_dict: Optional[Dict] = None,
                        json_dict: Optional[Dict] = None,
                        ) -> Dict:
    """Constructs dictionary of relevant BIDS related information that includes subject and session IDs, in addition
    to various metadata. Custom BIDS fields can also be added through the metadata dictionary.

    More information can be obtained from: 
        https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html.

    Usage example:
        >>> bids_dict = construct_bids_dict(meta_dict,
        ...                                 json_dict)
        ...

    Arguments:
        meta_dict: Metadata dictionary that contains the relevant BIDS metadata.
        json_dict: Dictionary constructed from the BIDS JSON file, or some secondary dictionary.

    Returns:
        Dictionary containing BIDS related metadata.
    
    Raises:
        IndexError: Error that arises if constant variables ``BIDS_INFO``'s keys and ``BIDS_ORD_ARR`` are of different lengths.
    """
    # BIDS informatino dictionary
    bids_info: Dict = deepcopy(BIDS_INFO)

    # OrderedDict array/list
    ordered_array: List[str] = deepcopy(BIDS_ORD_ARR)

    # Check that length of constant variables' indices are of the same length
    if len(list(bids_info.keys())) == len(ordered_array):
        pass
    else:
        raise IndexError("Input dictionary keys do not match ordered array. Check constant variables.")

    bids_dict: Dict = {}

    if meta_dict:
        pass
    else:
        meta_dict: Dict = {}
    
    if json_dict:
        pass
    else:
        json_dict = {}
    
    # Update BIDS ordered array
    meta_list: List[str] = list(meta_dict.keys())
    ordered_array.extend(meta_list)
    ordered_list: List[str] = []

    for word in ordered_array:
        # Check if the BIDS metadata field is valid
        if is_camel_case(word,bids_case=True):
            pass
        else:
            raise BIDSMetaDataError(f"Input metadata: {word} is not BIDS compliant.")
        
        # Add field to ordered array
        if word in ordered_list:
            pass
        else:
            ordered_list.append(word)
    
    # Create BIDS dictionary
    bids_dict: Dict = dict_multi_update(dictionary=None, **bids_info)
    bids_dict: Dict = dict_multi_update(dictionary=bids_dict, **meta_dict)
    bids_dict: Dict = dict_multi_update(dictionary=bids_dict, **json_dict)
    
    # Create ordered BIDS dictionary and drop unfilled metadata fields from ordered BIDS dictionary
    ordered_bids_dict: OrderedDict = OrderedDict()
    for key in ordered_list:
        val = bids_dict.get(key,'')
        if (val == "") or (val is None):
            continue
        elif (key == "EffectiveEchoSpacing") or (key == "TotalReadoutTime"):
            # NOTE: These two keys are being excluded entirely, as the current
            #   calculations fail BIDS validation.
            # TODO: Accurately compute 'EffectiveEchoSpacing' and 'TotalReadoutTime'
            continue
        else:
            ordered_bids_dict[key] = bids_dict[key]
    
    return ordered_bids_dict

def construct_bids_name(sub_data: SubDataInfo,
                        modality_type: Optional[str] = "",
                        modality_label: Optional[str] = "",
                        acq: Optional[str] = "",
                        ce: Optional[str] = "",
                        task: Optional[str] = "",
                        acq_dir: Optional[str] = "",
                        rec: Optional[str] = "",
                        run: Optional[Union[int,str]] = "",
                        echo: Optional[Union[int,str]]  = "",
                        case1: bool = False,
                        mag2: bool = False,
                        case2: bool = False,
                        case3: bool = False,
                        case4: bool = False,
                        out_dir: Optional[str] = "",
                        zero_pad: Optional[int] = 0
                        ) -> Dict:
    """Constructs BIDS filenames dictionary from input parameter descriptions.

    More information can be obtained from: 
        https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html.

    Usage example:
        >>> bids_param = construct_bids_name(sub_data=sub_data,
        ...                                  modality_type='func',
        ...                                  modality_label='bold',
        ...                                  task='rest',
        ...                                  run='01')
        ...

    Arguments:
        sub_data: SubDataInfo object that contains subject and session ID.
        modality_type: Modality type associated with the data. Valid modality types include, but are not limited to:

            * ``anat``: Anatomical scans
            * ``func``: Functional scans
            * ``dwi``: Diffusion weighted image scans
            * ``fmap``: Fieldmaps
            * ``swi``: Susceptibility weighted image scans

        modality_label: Modality label of associated with the data. Valid modality labels include, but are not limited to:

            * ``T1w``, ``T2w``, ``PD``, ``FLAIR``, ``T1rho`` (in the case of ``anat``).
            * ``bold``, ``cbv``, ``phase`` (in the case of ``func``).

            NOTE: 
                In the case of ``func`` modalities, these are referred to as ``contrast_labels`` in the BIDS documentation.

        acq: Acquisition description of the associated image data.
        ce: Contrast enhanced description of the associated image data.
        task: Task associated with the image data, required if ``func`` is used as the modality_type.
        acq_dir: Acquisition direction of the image (e.g. PA, AP, LR, RL).
        rec: Image reconstruction description.
        run: Run number of the associated image data.
        echo: Echo number of the associated image data (, in the case of multi-echo data).
        case1: BIDS fieldmap case 1, set to True if the following files are present:

            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phasediff.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phasediff.json``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_magnitude1.nii[.gz]``
            * ``[ sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_magnitude2.nii[.gz] ]``

        mag2: Should be set to True, if case 1 contains a second magnitude image.
        case2: BIDS fieldmap case 2, set to True if the following files are present:

            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phase1.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phase1.json``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phase2.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_phase2.json``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_magnitude1.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_magnitude2.nii[.gz]``

        case3: BIDS fieldmap case 3, set to True if the following files are present:

            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_magnitude.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_fieldmap.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_run-<index>]_fieldmap.json``

        case4: BIDS fieldmap case 4, set to True if the following files are present:

            * ``sub-<label>[_ses-<label>][_acq-<label>][_ce-<label>]_dir-<label>[_run-<index>]_epi.nii[.gz]``
            * ``sub-<label>[_ses-<label>][_acq-<label>][_ce-<label>]_dir-<label>[_run-<index>]_epi.json``

        out_dir: Target output directory for a subject's BIDS files.
        zero_pad: Number of zeroes to zeropad the output value.

    Returns:
        Nested dictionary that contains the necessary information to name BIDS files.
    
    Raises:
        BIDSNameError: Error raised if:
            * ``anat`` is the speicified modality_type, but no modality_label is specified.
            * ``func`` is the speicified modality_type, but no modality_label is specified.
            * ``func`` is the speicified modality_type, but no task is specified.
            * ``fmap`` is the speicified modality_type, but no fieldmap 'case' is specified.
    """
    # BIDS parameter dictionary
    bids_param: Dict = deepcopy(BIDS_PARAM)

    # Update subject and session ID in BIDS parameter dictionary
    bids_param["info"].update({"sub":sub_data.sub,
                               "ses":sub_data.ses})

    if modality_type.lower() == 'anat':
        if not modality_label:
            raise BIDSNameError("Modality label required for anatomical data (e.g. 'T1w').")
        bids_param["anat"]["acq"] = acq
        bids_param["anat"]["ce"] = ce
        bids_param["anat"]["rec"] = rec
        bids_param["anat"]["run"] = run
        bids_param["anat"]["modality_label"] = modality_label
    elif modality_type.lower() == 'func':
        if not modality_label:
            raise BIDSNameError("Contrast/modality label required for functional data (e.g. 'bold').")
        if not task:
            raise BIDSNameError("Task label required for functional data.")
        bids_param["func"]["task"] = task
        bids_param["func"]["acq"] = acq
        bids_param["func"]["ce"] = ce
        bids_param["func"]["dir"] = acq_dir
        bids_param["func"]["rec"] = rec
        bids_param["func"]["run"] = run
        bids_param["func"]["echo"] = echo
        bids_param["func"]["modality_label"] = modality_label
    elif modality_type.lower() == 'dwi':
        if not modality_label:
            modality_label = "dwi"
        bids_param["dwi"]["acq"] = acq
        bids_param["dwi"]["dir"] = acq_dir
        bids_param["dwi"]["run"] = run
        bids_param["dwi"]["modality_label"] = modality_label
    elif modality_type.lower() == 'fmap':
        bids_param["fmap"]["acq"] = acq
        bids_param["fmap"]["run"] = run
        if case1:
            bids_param["fmap"]["case1"]["phasediff"] = "phasediff"
            bids_param["fmap"]["case1"]["magnitude1"] = "magnitude1"
            if mag2:
                bids_param["fmap"]["case1"]["magnitude2"] = "magnitude2"
        elif case2:
            bids_param["fmap"]["case2"]["phase1"] = "phase1"
            bids_param["fmap"]["case2"]["phase2"] = "phase2"
            bids_param["fmap"]["case2"]["magnitude1"] = "magnitude1"
            bids_param["fmap"]["case2"]["magnitude2"] = "magnitude2"
        elif case3:
            bids_param["fmap"]["case3"]["magnitude"] = "magnitude"
            bids_param["fmap"]["case3"]["fieldmap"] = "fieldmap"
        elif case4:
            bids_param["fmap"]["ce"] = ce
            bids_param["fmap"]["dir"] = acq_dir
            bids_param["fmap"]["modality_label"] = 'epi'
        else:
            raise BIDSNameError("Fieldmap data was specified, however, no BIDS fieldmap case was specified.")
    elif modality_type:
        bids_param.update({modality_label:{"acq":acq,
                                           "ce":ce,
                                           "dir":acq_dir,
                                           "rec":rec,
                                           "run":run,
                                           "echo":echo,
                                           "modality_label": modality_label}})
    elif modality_type == "":
        if not modality_label:
            modality_label = "unknown"
        bids_param.update({"unknown":{"task":task,
                                      "acq":acq,
                                      "ce":ce,
                                      "dir":acq_dir,
                                      "rec":rec,
                                      "run":run,
                                      "echo":echo,
                                      "modality_label":modality_label}})

    # Obtain run number if not specified
    if run is None or run == "":
        if out_dir:
            run = num_runs(directory=out_dir,
                           modality_type=modality_type,
                           modality_label=modality_label,
                           bids_dict=bids_param,
                           zero_pad=zero_pad)
        else:
            run = zeropad(num=1,num_zeros=zero_pad)
        
        # Back track to fill in run number
        bids_param = construct_bids_name(sub_data=sub_data,
                                         modality_type=modality_type,
                                         modality_label=modality_label,
                                         acq=acq,
                                         ce=ce,
                                         task=task,
                                         acq_dir=acq_dir,
                                         rec=rec,
                                         run=run,
                                         echo=echo,
                                         case1=case1,
                                         mag2=mag2,
                                         case2=case2,
                                         case3=case3,
                                         case4=case4)

    return bids_param

def num_runs(directory: Optional[str] = "",
             modality_type: Optional[str] = "",
             modality_label: Optional[str] = "",
             bids_dict: Optional[Dict] = None,
             zero_pad: Optional[int] = None
             ) -> Union[int,str]:
    """Counts the number of similarly named files in a directory to obtain a unique run number.
    Optimal use of this function requires the:

        * search directory (``directory``)
        * modality type (``modality_type``)
        * BIDS filename dictionary (``bids_dict``)
    
    NOTE: 
        The optional input ``bids_dict`` is a nested dictionary constructed by the function ``construct_bids_name``.
    
    Usage example:
        >>> num_runs(directory: str,
        ...          modality_type='func',
        ...          modality_label='bold,
        ...          bids_dict=bids_dict,
        ...          zero_pad=3)
        '001'

    Arguments:
        directory: Input directory to search.
        modality_type: Modality type associated with the data. Valid modality types include, but are not limited to:

            * ``anat``: Anatomical scans
            * ``func``: Functional scans
            * ``dwi``: Diffusion weighted image scans
            * ``fmap``: Fieldmaps
            * ``swi``: Susceptibility weighted image scans

        modality_label: Modality label of associated with the data. Valid modality labels include, but are not limited to:

            * ``T1w``, ``T2w``, ``PD``, ``FLAIR``, ``T1rho`` (in the case of ``anat``).
            * ``bold``, ``cbv``, ``phase`` (in the case of ``func``).

            NOTE: 
                In the case of ``func`` modalities, these are referred to as "contrast_labels" in the BIDS documentation.

        bids_dict: Nested BIDS name dictionary that contains relevant information to naming files.
        zero_pad: Number of zeroes to zeropad the output value.

    Returns:
        Integer (or string should the value be zeropadded).
    """
    if os.path.exists(directory):
        directory: str = os.path.abspath(directory)
    elif zero_pad:
        return zeropad(num=1,num_zeros=zero_pad)
    else:
        return 1
    
    if modality_type and modality_label and not bids_dict:
        glob_str: str = os.path.join(directory,f"*{modality_label}*{modality_type}*.nii*")
        runs: str = os.path.join(directory,f"*{glob_str}.nii*")
        num: int = len(glob.glob(runs)) + 1

        if zero_pad:
            return zeropad(num=num,num_zeros=zero_pad)
        else:
            return num
    
    if bids_dict:
        pass
    elif zero_pad:
        return zeropad(num=1,num_zeros=zero_pad)
    else:
        return 1
    
    # Construct glob string
    tmp_list: List[str] = []
    try:
        for item in list(bids_dict[modality_type].keys()):
            if bids_dict[modality_type][item] == "":
                pass
            elif isinstance(bids_dict[modality_type][item], dict):
                for id,name in bids_dict[modality_type][item].items():
                    if bids_dict[modality_type][item][id] == "":
                        pass
                    else:
                        tmp_list.append(name)
                        tmp_list.append("*")
            else:
                tmp_list.append(bids_dict[modality_type][item])
                tmp_list.append("*")
    except KeyError:
        pass
    glob_str: str = ''.join(tmp_list)
    runs: str = os.path.join(directory,f"*{glob_str}.nii*")
    num: int = len(glob.glob(runs)) + 1

    if zero_pad:
        return zeropad(num=num,num_zeros=zero_pad)
    else:
        return num

def search_bids(s: str,
                bids_search: Optional[Dict] = None,
                bids_map: Optional[Dict] = None,
                modality_type: Optional[str] = "",
                modality_label: Optional[str] = "",
                task: Optional[str] = "",
                bids_name_dict: Optional[Dict] = {}
                ) -> Dict:
    """Performs search of BIDS (or related terms) provided there are ``bids_search``, and ``bids_map`` dictionaries, and some input
    string (or file, represented as a string).
    
    Usage example:
        >>> bids_name_dict = search_bids("image_file_0001.dcm",
        ...                              bids_search=bids_search_dict,
        ...                              bids_map=bids_map_dict,
        ...                              modality_type="func",
        ...                              modality_label="bold",
        ...                              task="rest")
        ...
        
    Arguments:
        s: Input string (or file, represented as a string).
        bids_search: Heurestic BIDS related search terms.
        bids_map: Descriptive BIDS terms to be mapped to.
        modality_type: Modality type (e.g. ``anat``, ``func``, ``dwi`` etc).
        modality_label: Modality label (e.g. ``T1w``, ``bold``, ``dwi`` etc).
        task: Task label.
        bids_name_dict: Existing BIDS name dictionary.
        
    Returns:
        Nested dictionary of BIDS descriptive naming related terms.
    """
    if bids_name_dict:
        bids_name_dict: Dict = deepcopy(bids_name_dict)
    else:
        bids_name_dict: Dict = deepcopy(BIDS_PARAM)
    
    if modality_type and modality_label and bids_search and bids_map:
        pass
    elif modality_type and modality_label:
        if task:
            bids_name_dict[modality_type]['modality_label'] = modality_label
            bids_name_dict[modality_type]['task'] = task
        else:
            bids_name_dict[modality_type]['modality_label'] = modality_label
        return bids_name_dict
    
    if depth(bids_search[modality_type]) == 3:
        try:
            for (k1,v1),(k2,v2) in zip(bids_search[modality_type][modality_label].items(),bids_map[modality_type][modality_label].items()):
                    for va,vb in zip(v1,v2):
                        if list_in_substr(in_list=[va],in_str=s):
                            bids_name_dict[modality_type]['modality_label'] = modality_label
                            bids_name_dict[modality_type][k1] = vb
                        else:
                            bids_name_dict[modality_type]['modality_label'] = modality_label
        except (TypeError,KeyError):
            pass
    elif depth(bids_search[modality_type]) == 4:
        try:
            for (k1,v1),(k2,v2) in zip(bids_search[modality_type][modality_label][task].items(),bids_map[modality_type][modality_label][task].items()):
                    for (va,vb) in zip(v1,v2):
                        if list_in_substr(in_list=[va],in_str=s):
                            bids_name_dict[modality_type]['modality_label'] = modality_label
                            bids_name_dict[modality_type]['task'] = task
                            bids_name_dict[modality_type][k1] = vb
                        else:
                            bids_name_dict[modality_type]['modality_label'] = modality_label
                            bids_name_dict[modality_type]['task'] = task
        except (TypeError,KeyError):
            pass
    
    return bids_name_dict
