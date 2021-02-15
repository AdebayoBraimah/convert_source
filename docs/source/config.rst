-------------------
Configuration File
-------------------

The ``YAML`` (``.yml``) configuration file dictates what modalities and parameter information
is used to write the BIDS NIFTI files, in addition to its associated metadata.

Configuration File Keywords
-----------------------------

The configuration file will look for these 5 distinct keywords:

* ``modality_search``: Heuristic search terms for each modality (**required**).
* ``bids_search``: Heuristic search terms for each BIDS related filename description.
* ``bids_map``: Corresponding terms to map ``bids_search``'s search terms to.
* ``metadata``: The metadata to write to each image file's JSON (sidecar) file.
* ``exclude``: Files and/or modalities to exclude that contain any words in this list.

``modality_search``
=====================

The ``modality_search`` keyword is required and serves several purposes. 
The main purpose of this keyword is that it provides a mapping between the
intended BIDS ``modality_label`` and some corresponding heuristic search terms.
Secondly, this keyword directly dictates the BIDS directory layout for each subject.

.. code-block:: yaml

    # Heurestic search terms for each modality

    modality_search:        # Configuration file modality_search keyword
        anat:               # BIDS modality type (for anatomical images)
            T1w:            # BIDS modality label (for T1w images)
                - T1        # Heurestic search terms list (for T1w images)     
                - T1w
                - TFE
            T2w:            # BIDS modality label (for T2w images)
                - T2        # Heurestic search terms list (for T2w images)
                - T2w
                - TSE
            flair:          # BIDS modality label (for FLAIR images)
                - flair     # Heurestic search terms list (for FLAIR images)
                    .
                    .
                    .

Additionally, the corresponding BIDS directory layout this would create would look like:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   └── anat
    |       ├── sub-001_run-01_T1w.json
    |       ├── sub-001_run-01_T1w.nii.gz
    |       ├── sub-001_run-01_T2w.json
    |       ├── sub-001_run-01_T2w.nii.gz
    |       ├── sub-001_run-01_flair.json
    |       └── sub-001_run-01_flair.nii.gz
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    .
    .
    .
    ├── unknown
    ├──.bidsignore
    └──.misc

This schema can be further extended to accomdate other BIDS related modality types and labels as shown below:

.. code-block:: yaml

    # Heurestic search terms for each modality

    modality_search:            # Configuration file modality_search keyword
        dwi:                    # BIDS modality type (for diffusion weighted images, DWI)
            dwi:                # BIDS modality label (for DWIs)
                - diffusion     # Heurestic search terms list (for DWIs)
                - DTI
                - DWI
        fmap:                   # BIDS modality type (for field maps)
            fmap:               # BIDS modality label (for field maps)
                - fieldmap      # Heurestic search terms list (for field maps)    
                - map
                    .
                    .
                    .

The above schema would produce the following BIDS output directory layout:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   ├── anat
    |   ├── dwi
    |   |   ├── sub-001_run-01_dwi.bval
    |   |   ├── sub-001_run-01_dwi.bvec
    |   |   ├── sub-001_run-01_dwi.json
    |   |   └── sub-001_run-01_dwi.nii.gz
    |   └── fmap
    |       ├── sub-001_run-01_magnitude.nii.gz
    |       ├── sub-001_run-01_fieldmap.nii.gz
    |       └── sub-001_run-01_fieldmap.json
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    .
    .
    .
    ├── unknown
    ├──.bidsignore
    └──.misc

Functional Task Data
++++++++++++++++++++++

Functional task data is handled similarly, with the task name being included in the search list as shown below:

.. code-block:: yaml

    # Heurestic search terms for each modality

    modality_search:            # Configuration file modality_search keyword
        func:                   # BIDS modality type (for functional images)
            bold:               # BIDS modality label (, or contrast label for functional BOLD images)
                rest:           # BIDS task name
                    - rsfMR     # Heurestic search terms list (for functional BOLD images with resting state task)
                    - rest
                    - FFE
                    - FEEPI
                nback:          # BIDS task name
                    - nback     # Heurestic search terms list (for functional BOLD images with N-back task)

            cbv:                # BIDS modality label (, or contrast label for functional CBV, cerebral bloold volume images)
                rest:           # BIDS task name
                    - casl      # Heurestic search terms list (for functional CBV images with resting state task)
                    - pcas
                        .
                        .
                        .

The corresponding BIDS output directory layout would look something like:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   ├── anat
    |   ├── dwi
    |   ├── fmap
    |   └── func
    |       ├── sub-001_run-01_bold.json
    |       ├── sub-001_run-01_bold.nii.gz
    |       ├── sub-001_run-01_sbref.json
    |       ├── sub-001_run-01_sbref.nii.gz
    |       ├── sub-001_run-01_cbv.json
    |       └── sub-001_run-01_cbv.nii.gz
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    .
    .
    .
    ├── unknown
    ├──.bidsignore
    └──.misc

.. warning:: The ``cbv`` ``modality_type`` may be deprecated in BIDS version 1.5+. LINK: https://bids-specification.readthedocs.io/en/latest/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#deprecated-suffixes

Non-BIDS Related Modalities
+++++++++++++++++++++++++++++

Non-BIDS related data may also be added to the configuration file to accomdate the study dataset.

To do so, see the example below:

.. code-block:: yaml

    # Heurestic search terms for each modality

    modality_search:        # Configuration file modality_search keyword
        swi:                # BIDS modality type (for SWIs)
            swi:            # BIDS modality label (for SWIs)
                - swi       # Heurestic search terms list (for SWIs)     
                - sw_image
                    .
                    .
                    .

The corresponding output BIDS directory layout would look like:

.. code-block:: none

    Output_Directory
    ├── sub-001
    |   ├── anat
    |   ├── dwi
    |   ├── fmap
    |   ├── func
    |   └── swi
    |       ├── sub-001_run-01_swi.json
    |       └── sub-001_run-01_swi.nii.gz
    ├── sub-002
    ├── sub-003
    ├── sub-004
    ├── sub-005
    .
    .
    .
    ├── unknown
    ├──.bidsignore
    └──.misc

Moreover, any non-BIDS related data can be accomdated by following this layout in the configuration file:

.. code-block:: yaml

    # Heurestic search terms for each modality

    modality_search:                # Configuration file modality_search keyword
        modality_type:              # Modality type 
            modality_label:         # Modality label
                - search_term_1     # Heurestic search terms list 
                - search_term_2
                    .
                    .
                    .

``bids_search`` & ``bids_map``
================================

The ``bids_search`` and ``bids_map`` keywords are optional and intended for a heurestic search and mapping (, respectively) for BIDS descriptive labels 
in the source data, and what the output BIDS filename should contain.
For example, subject 1 has a high resolution T1 weighted image stored in a DICOM directory as ``001/T1_HighRes_05mm/MR000001.dcm``. The output BIDS
NIFTI file should `preferably` have the ``acq`` field populated to reflect this: ``sub-001/anat/sub-001_acq-highres05mm_run-01_T1w.nii.gz``. This can be accomplished
in the configuration file as shown below: 

.. code-block:: yaml

    # Heurestic search terms for BIDS descriptive naming conventions

    bids_search:
        anat:
            T1w:
                acq:
                    - HighRes_05mm
                ce:
                rec:

    # BIDS terms to map to

    bids_map:
        anat:
            T1w:
                acq:
                    - highres05mm
                ce:
                rec:

.. warning:: As ``bids_search`` parameters can accept a multiple search terms, ``bids_map`` is only capable of mapping to only one term. For example:
    
    .. code-block:: yaml

        # Heurestic search terms for BIDS descriptive naming conventions

        bids_search:
            anat:
                T1w:
                    acq:
                        - HighRes_05mm
                        - HighRes_01mm
                    ce:
                    rec:

        # BIDS terms to map to

        bids_map:
            anat:
                T1w:
                    acq:
                        - highres05mm
                        - highres01mm
                    ce:
                    rec:

    This would result in only the last entry in ``bids_map`` for the ``acq`` field being written to the output NIFTI files that match these search terms (``sub-001/anat/sub-001_acq-highres01mm_run-01_T1w.nii.gz``) 
    despite the fact that files may be found that contain either `HighRes_05mm` or `HighRes_01mm` in their filename or file header.

.. note:: The work-around for this issue would be to use one set of search and map labels to process one set of files, while ignoring/excluding the other, followed by switching `HighRes_01mm` and `HighRes_05mm`, as shown below: 

    .. code-block:: yaml

        # Heurestic search terms for BIDS descriptive naming conventions

        bids_search:
            anat:
                T1w:
                    acq:
                        - HighRes_05mm
                    ce:
                    rec:

        # BIDS terms to map to

        bids_map:
            anat:
                T1w:
                    acq:
                        - highres05mm
                    ce:
                    rec:
        
        # Exclude/Ignore terms

        exclude:
            - HighRes_01mm

    This would achieve the desired output: ``sub-001/anat/sub-001_acq-highres05mm_run-01_T1w.nii.gz``.

``metadata``
=====================

The ``metadata`` keyword is optional, but strongly recommended. The ``metadata`` field in the configuration file will write 
the modality specific metadata for each NIFTI file's JSON (sidecar) file. Additionally, the word ``common`` may also be specified
under ``metadata`` to include metadata that is common between all of the study's source images.

For example:

.. code-block:: yaml

    metadata:
        common:
            Manufacturer: Philips
            ManufacturersModelName: Ingenia
            MagneticFieldStrength: 3
            InstitutionName: Cincinnati Children's Hospital Medical Center
        func:
            rest:
                ParallelAcquisitionTechnique: SENSE
                ParallelReductionFactorInPlane: 1.5
                MultibandAccelerationFactor: 2
                TaskName: Resting State
                TaskDescription: Resting state scan, in which the participant looks at a fixed cross (+).
            nback:
                ParallelAcquisitionTechnique: SENSE
                ParallelReductionFactorInPlane: 1.0
                MultibandAccelerationFactor: 1
                TaskName: N-back Task
                TaskDescription: Working memory task.
        fmap:
            Units: Hz

.. warning:: The metadata names for the fields above (e.g. ``TaskName``, ``InstitutionName``, ``MagneticFieldStrength`` etc.) must be in ``CamelCase`` otherwise, a ``BIDSMetaDataError`` exception will be raised.

``exclude``
============

Files and/or modalities that one wants ignored can be done by specifying the ``exclude`` keyword, 
followed by a list of words that the associated files/modalities would contain (and are not case sensitive). 
For example:

.. code-block:: yaml

    exclude:
        - SURVEY
        - ScreenCapture
        - ProtonDensity
        - PD            # Some ProtonDensity images may be labeled with this in the filename
        - T1Rho

The above example would simply ignore all files that contain these words - which would achieve the goal of excluding
files and/or image data that would generally correspond to:

* Survey images
* Secondary screen captures
* Proton Density images
* T1 rho images
