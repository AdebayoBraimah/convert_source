--------
Outputs
--------

Unknown
--------

The directory named ``unknown`` in the output directory is populated by NIFTI images
that could not be identified. Files in this directory are generally named following 
this convention: ``sub-<label>[ses-<label>]_run-<label>_unknown.nii.gz``, as shown in
the example below (assuming that this study only had one session).

.. code-block:: none

    Output_Directory
    ├── sub-001
    ├── sub-002
    .
    .
    .
    ├── unknown
    |   ├── sub-001_ses-001_run-01_unknown.json
    |   ├── sub-001_ses-001_run-01_unknown.nii.gz
    |   ├── sub-001_ses-001_run-02_unknown.json
    |   └── sub-001_ses-001_run-02_unknown.nii.gz
    ├──.bidsignore
    └──.misc

.misc
------

The ``.misc`` directory contains miscellaneous files that pertain to the image conversion
process, such as log files (as shown below).

.. code-block:: none

    Output_Directory
    ├── sub-001
    ├── sub-002
    .
    .
    .
    ├── unknown
    ├──.bidsignore
    └──.misc
        └── convert_source.log

.bidsignore
------------

The ``.bidsignore`` file is generated and intended for BIDS validation
after data conversion. This file acts similarly to the ``.gitignore``
file - meaning files that should be ignored in the output BIDS directory
should have their filenames written to this file. For example:

.. code-block:: bash

    # .bidsignore file

    unknown
    .misc

The ``unknown`` and ``.misc`` directories are not BIDS valid directories and as such,
would likely throw errors during BIDS validation.
