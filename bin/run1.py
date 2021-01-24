#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-

'''
TODO:
    - Add (hidden) log file directory and .gitignore file
    - Add simpler example configurations file
    - Add file handling capabilities of task csv/tsv files
        - use BIDSimg class to keep track of files
            or
        - create new class
    - Add option for creating sessions TSV file(s)
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
    # [X] Search, find, and categorize image data for each subject and each session
    #   - [X] The categorization should be prefereably stored as a dictionary,
    #       pickled, or as an object
    # Write/re-configure wrapper function(s) to convert image data
    #   - Re-configure directory layout and function handling.

