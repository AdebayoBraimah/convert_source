--------
Examples
--------

.. note:: The following examples shown below correspond to the directory layouts shwon in the Usage section.

Study Directory Layout 1
-------------------------

Command Line Interface
========================

In the case of **study directory layout 1**, the command would look like:

.. code-block:: bash

    $ study_proc \
    --study-dir=</path/to/study/directory> \
    --out-dir=</path/to/output/directory> \
    --compress=6 \
    --zero-pad=2 \
    --append-dwi-info \
    --verbose

Python Module Interface
=========================

Likewise, in python:

.. code-block:: python

    from convert_source.batch_convert import batch_proc

    [imgs, jsons, bvals, bvecs] = batch_proc(study_img_dir='</path/to/study/directory>',
    ...                                      out_dir='</path/to/output/directory>',
    ...                                      append_dwi_info=True,
    ...                                      zero_pad=2,
    ...                                      cprss_lvl=6,
    ...                                      verbose=True)
    ...

**The corresponding output from both commands** yeilds the follwing BIDS output directory:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   └── ses-001
    |       ├── anat
    |       |   ├── sub-001_ses-001_run-01_T1w.json
    |       |   └── sub-001_ses-001_run-01_T1w.nii.gz
    |       ├── dwi
    |       |   ├── sub-001_ses-001_acq-TE88_run-01_sbref.json
    |       |   ├── sub-001_ses-001_acq-TE88_run-01_sbref.nii.gz
    |       |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.bval
    |       |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.bvec
    |       |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.json
    |       |   └── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.nii.gz
    |       ├── func
    |       |   ├── sub-001_ses-001_run-01_bold.json
    |       |   ├── sub-001_ses-001_run-01_bold.nii.gz
    |       |   ├── sub-001_ses-001_run-01_sbref.json
    |       |   └── sub-001_ses-001_run-01_sbref.nii.gz
    |       └── fmap
    |           ├── sub-001_ses-001_run-01_magnitude.nii.gz
    |           ├── sub-001_ses-001_run-01_fieldmap.nii.gz
    |           └── sub-001_ses-001_run-01_fieldmap.json
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    ├── sub-006
    ├── sub-007
    ├── sub-008
    ├── sub-009
    ├── sub-010
    ├── sub-011
    ├── sub-012
    ├── sub-013
    └── sub-014

Study Directory Layout 2
-------------------------

Using the same commands from above on **study directory layout 2**, we get the following BIDS output directory layout:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   ├── anat
    |   |   ├── sub-001_run-01_T1w.json
    |   |   └── sub-001_run-01_T1w.nii.gz
    |   ├── dwi
    |   |   ├── sub-001_acq-TE88_run-01_sbref.json
    |   |   ├── sub-001_acq-TE88_run-01_sbref.nii.gz
    |   |   ├── sub-001_acq-b800b1500b2000TE88_run-01_dwi.bval
    |   |   ├── sub-001_acq-b800b1500b2000TE88_run-01_dwi.bvec
    |   |   ├── sub-001_acq-b800b1500b2000TE88_run-01_dwi.json
    |   |   └── sub-001_acq-b800b1500b2000TE88_run-01_dwi.nii.gz
    |   ├── func
    |   |   ├── sub-001_run-01_bold.json
    |   |   ├── sub-001_run-01_bold.nii.gz
    |   |   ├── sub-001_run-01_sbref.json
    |   |   └── sub-001_run-01_sbref.nii.gz
    |   └── fmap
    |       ├── sub-001_run-01_magnitude.nii.gz
    |       ├── sub-001_run-01_fieldmap.nii.gz
    |       └── sub-001_run-01_fieldmap.json
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    ├── sub-006
    ├── sub-007
    ├── sub-008
    ├── sub-009
    ├── sub-010
    ├── sub-011
    ├── sub-012
    ├── sub-013
    └── sub-014

Study Directory Layout 3
-------------------------

Likewise with **study directory layout 3**:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   ├── ses-001
    |   |   ├── anat
    |   |   |   ├── sub-001_ses-001_run-01_T1w.json
    |   |   |   └── sub-001_ses-001_run-01_T1w.nii.gz
    |   |   ├── dwi
    |   |   |   ├── sub-001_ses-001_acq-TE88_run-01_sbref.json
    |   |   |   ├── sub-001_ses-001_acq-TE88_run-01_sbref.nii.gz
    |   |   |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.bval
    |   |   |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.bvec
    |   |   |   ├── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.json
    |   |   |   └── sub-001_ses-001_acq-b800b1500b2000TE88_run-01_dwi.nii.gz
    |   |   ├── func
    |   |   |   ├── sub-001_ses-001_run-01_bold.json
    |   |   |   ├── sub-001_ses-001_run-01_bold.nii.gz
    |   |   |   ├── sub-001_ses-001_run-01_sbref.json
    |   |   |   └── sub-001_ses-001_run-01_sbref.nii.gz
    |   |   └── fmap
    |   |       ├── sub-001_ses-001_run-01_magnitude.nii.gz
    |   |       ├── sub-001_ses-001_run-01_fieldmap.nii.gz
    |   |       └── sub-001_ses-001_run-01_fieldmap.json
    |   └── ses-002
    |       ├── anat
    |       |   ├── sub-001_ses-002_run-01_T1w.json
    |       |   └── sub-001_ses-002_run-01_T1w.nii.gz
    |       ├── dwi
    |       |   ├── sub-001_ses-002_acq-TE88_run-01_sbref.json
    |       |   ├── sub-001_ses-002_acq-TE88_run-01_sbref.nii.gz
    |       |   ├── sub-001_ses-002_acq-b800b1500b2000TE88_run-01_dwi.bval
    |       |   ├── sub-001_ses-002_acq-b800b1500b2000TE88_run-01_dwi.bvec
    |       |   ├── sub-001_ses-002_acq-b800b1500b2000TE88_run-01_dwi.json
    |       |   └── sub-001_ses-002_acq-b800b1500b2000TE88_run-01_dwi.nii.gz
    |       ├── func
    |       |   ├── sub-001_ses-002_run-01_bold.json
    |       |   ├── sub-001_ses-002_run-01_bold.nii.gz
    |       |   ├── sub-001_ses-002_run-01_sbref.json
    |       |   └── sub-001_ses-002_run-01_sbref.nii.gz
    |       └── fmap
    |           ├── sub-001_ses-002_run-01_magnitude.nii.gz
    |           ├── sub-001_ses-002_run-01_fieldmap.nii.gz
    |           └── sub-001_ses-002_run-01_fieldmap.json
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    ├── sub-006
    ├── sub-007
    ├── sub-008
    ├── sub-009
    ├── sub-010
    ├── sub-011
    ├── sub-012
    ├── sub-013
    └── sub-014

