#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-

'''
TODO:
    - Enable gzipping/gunzipping utility function(s) for cases when interacting with 
        uncompressed image files.
            - Or in the case the desired output files need to be uncompressed. 
            - Should have option for native gzipping/gunzipping in the case of 
                U/NIX systems
    - Add (hidden) log file directory and .gitignore file
    - Add simpler example configurations file
'''

from utils.command_utils import Command, DependencyError

def batch_convert():

    # [X] Read configurations file, and define search terms
    #   - [X] Store search terms, exclusion list, and metadata
    # [X] Iterate through parent directory, and get subject IDs and session IDs
    #   - [X] Store as object that contains:
    #       - [X] subject ID 
    #       - [X] session ID [if present]
    #       - [X] path to data directory
    # [X] Convert source data to NIFTI
    #   - [X] Use TmpDir context manager to create tmp dir to glob files
    #       for the function return
    #   - [X] Files are returned as tuple of lists (maybe should be object)?
    # Search, find, and categorize image data for each subject and each session
    #   - The categorization should be prefereably stored as a dictionary,
    #       pickled, or as an object

