------
Usage
------

.. argparse::
    :ref: convert_source.bin.study_proc.arg_parser
    :prog: convert_source
    :nodefault:
    :nodefaultconst:

Study Directory Layout
-----------------------

The study directory layout shown below is for a study consisting of 14 subjects, each with one session.

.. code-block:: none

    Study_Image_Directory
    ├── 001-001
    ├── 002-001
    ├── 003-001
    ├── 004-001
    ├── 005-001
    ├── 006-001
    ├── 007-001
    ├── 008-001
    ├── 009-001
    ├── 010-001
    ├── 011-001
    ├── 012-001
    ├── 013-001
    └── 014-001

In the case of a study with only one session, the directory layout could also be as shown: 

.. code-block:: none

    Study_Image_Directory
    ├── 001
    ├── 002
    ├── 003
    ├── 004
    ├── 005
    ├── 006
    ├── 007
    ├── 008
    ├── 009
    ├── 010
    ├── 011
    ├── 012
    ├── 013
    └── 014


This layout is for a study of 7 subjects with 2 sessions.

.. code-block:: none

    Study_Image_Directory
    ├── 001-001
    ├── 001-002
    ├── 002-001
    ├── 002-002
    ├── 003-001
    ├── 003-002
    ├── 004-001
    ├── 004-002
    ├── 005-001
    ├── 005-002
    ├── 006-001
    ├── 006-002
    ├── 007-001
    └── 007-002
       

Subject Directory Layout
------------------------

Each subject's directory should consist of image files, or in the case shown below, nested
directories of image files.

.. code-block:: none

    Study_Image_Directory
    └── 001-001
        ├── DICOM
        │   └── ST000000
        │       ├── SE000000
        │       │   └── MR000002.dcm
        │       ├── SE000001
        │       │   ├── MR000001.dcm
        │       │   .
        │       │   .
        │       │   .
        │       │   └── MR000056.dcm
        │       └── SE000002
        │           ├── MR000000.dcm
        │           .
        │           .
        │           .
        │           └── MR000015.dcm
        ├── NIFTI
        │   ├── DWI_68_DIR.bvec
        │   ├── DWI_68_DIR.bval
        │   ├── DWI_68_DIR.json
        │   ├── DWI_68_DIR.nii.gz
        │   ├── DWI_B0.json
        │   ├── DWI_B0.nii.gz
        │   ├── rsfMRI.json
        │   ├── rsfMRI.nii.gz
        │   ├── T1_AXIAL.json
        │   └── T1_AXIAL.nii.gz
        └── PAR REC
            ├── AXIAL.PAR
            ├── AX_SWIP_MPR.PAR
            ├── B0_DWI.PAR
            └── DWI_MB4_SENSE_1_3.PAR

Some text here...
