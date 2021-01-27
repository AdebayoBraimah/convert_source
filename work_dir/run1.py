#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-

'''
TODO:
    - Remove all .DS_STORE files and add it to .gitignore.
    - NEED to make sure that session ID is either included or excluded, but cannot be inconsistent.
    - Add option to use dcm2nii to image conversion function.
    - Add (hidden) log file directory and .bidsignore file
    - Add simpler example configurations file
    - Add file handling capabilities of task csv/tsv files
        - use BIDSimg class to keep track of files
            or
        - create new class
    - Add option for creating sessions TSV file(s)
'''

def batch_convert():

    # [X] Read configurations file, and define search terms
    #   - [X] Store search terms, exclusion list, and metadata
    # [X] Iterate through parent directory, and get subject IDs and session IDs
    #   - [X] Store as object that contains:
    #       - [X] subject ID 
    #       - [X] session ID [if present]
    #       - [X] path to data directory
    # [X] Search, find, and categorize image data for each subject and each session
    #   - [X] The categorization should be prefereably stored as a dictionary,
    #       pickled, or as an object
    # Write/re-configure wrapper function(s) to convert image data
    #   - Re-configure directory layout and function handling.
    # [X] Convert source data to NIFTI
    #   - [X] Use TmpDir context manager to create tmp dir to glob files
    #       for the function return
    #   - [X] Files are returned as tuple of lists (maybe should be object)?

    return None