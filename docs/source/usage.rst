------
Usage
------

Command Line Interface
-----------------------

.. code-block:: none

    usage: study_proc [-h] [-s STUDY_DIR] [-o OUT_DIR] [-c CONFIG.yml] [--no-gzip]
                      [--compress INT] [--zero-pad INT] [--append-dwi-info]
                      [--verbose] [--version] [--path-env PATH_VAR]

    Convert source data of a study's imaging data to BIDS NIFTI data.

    optional arguments:
      -h, --help            show this help message and exit

    Required Argument(s):
      -s STUDY_DIR, -study STUDY_DIR, --study-dir STUDY_DIR
                            Parent study image directory for all subjects.
      -o OUT_DIR, -out OUT_DIR, --out-dir OUT_DIR
                            Output directory.

    Optional Argument(s):
      -c CONFIG.yml, -config CONFIG.yml, --config-file CONFIG.yml
                            Input YAML configuration file. If no configuration
                            file is provided, then the default configuration file
                            is used.
      --no-gzip             DO NOT gzip the resulting BIDS NIFTI files [default:
                            False].
      --compress INT        Compression level [1 - 9] - 1 is fastest, 9 is
                            smallest [default: 6].
      --zero-pad INT        The amount of zeropadding to pad the run numbers of
                            the BIDS NIFTI files (e.g. '--zero-pad=2' corresponds
                            to '01') [default: 2].
      --append-dwi-info     RECOMMENDED: Appends DWI acquisition information
                            (unique non-zero b-values, and TE, in msec.) to BIDS
                            acquisition filename of diffusion weighted image files
                            [default: False].
      --verbose             Enables verbose output to the command line.
      --version             Prints the version of 'convert_source', then exits.

    Expert Option(s):
      --path-env PATH_VAR   Environmental path variable or variables for
                            dependencies (e.g. the path to 'dcm2niix'). NOTE: This
                            option is repeatable, and can thus be specified
                            multiple times.

Python Module Interface
------------------------

.. code-block:: python

    from convert_source.batch_convert import batch_proc

    [imgs, jsons, bvals, bvecs] = batch_proc(study_img_dir='</path/to/study/directory>',
    ...                                      out_dir='</path/to/output/directory>',
    ...                                      gzip=True,
    ...                                      append_dwi_info=True,
    ...                                      zero_pad=2,
    ...                                      cprss_lvl=6)
    ...


Study Directory Layout
-----------------------

.. note:: The following directory layouts shown below are used in the following examples in the examples section.


Study Directory Layout 1
========================

For ``convert_source`` to infer each subject's and session ID correctly, the study directory layout must conform to one of the layouts shown below.

The study directory layout shown here is for a study consisting of 14 subjects, each with one session.

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

Study Directory Layout 2
=========================

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

Study Directory Layout 3
========================

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

