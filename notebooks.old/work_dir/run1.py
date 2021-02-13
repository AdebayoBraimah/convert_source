#!/usr/bin/env python3
# 
# -*- coding: utf-8 -*-

'''
TODO:
    - Decide if image is T1 or T2 using TR and TE.
    - NEED to make sure that session ID is either included or excluded, but cannot be inconsistent.
    - Add file handling capabilities of task csv/tsv files
    - Add option for creating sessions TSV file(s)
'''

# Changes to commit:
#   * Updated TODOs

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