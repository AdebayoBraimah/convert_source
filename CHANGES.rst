CHANGES
=========

0.2.0a11
---------

This version is an alpha release that contains several bug fixes and updates.

* BUG FIX: 

0.2.0a10
---------

This version is an alpha release that contains several bug fixes and updates.

* BUG FIX: Removed gzip/gunzip file checks, as this caused file and BIDS validation issues.
* BUG FIX: Added support for all caps BIDS metadata, and exclusion of non-BIDS metadata rather than raising exceptions.

0.2.0a9
---------

This version is an alpha release that contains several bug fixes and updates.

* BUG FIX: Fixed issue in which multiple converted NIFTI files would throw index error exception during BIDS renaming.
* BUG FIX: Added minimal type checking for several BIDS metadata fields
* BUG FIX: Fixed bug in which if par/nii was in the filepath, the source image file could be misclassified - thus subsequently throwing errors.
* UPDATE: Added option to throw exceptions for PAR multi-echo data. At the moment, without test data correctly handling cases of multi-echo data are not possible for PAR REC data.

0.2.0a8
---------

This version is an alpha release that contains several bug fixes and updates.

* BUG FIX: Fixed bug in which an unexpected parent DICOM directory could throw errors.
* BUG FIX: Fixed bug in which BIDS related parameters were not added to the output file name.
* UPDATE: More robust and reliable BIDS file naming.
* ENHANCEMENT: Added support for native symbolic linking.

0.2.0a7
---------

This version is an alpha release that contains several bug fixes and updates.

* BUG FIX: Fixed bug in which ``sbrefs`` were not written to subjects' ``scans.tsv`` files.
* BUG FIX: Fixed bug in which diffusion weighted image information was appended, despite not being indicated to do so.
* BUG FIX: Fixed bug in which either corrupted or inaptly named were either not compressed/uncompressed.
* UPDATE: Log output has been re-formatted to be more readable.

0.2.0a6
---------

This version is an alpha release that contains several bug fixes.

* BUG FIX: Removed the ``metadata`` fields ``EffectiveEchoSpacing`` and ``TotalReadoutTime`` as these fields were computed incorrectly, and thus failing BIDS validation.
* BUG FIX: Fixed issue in which zero and non-zero b-values were included in the ``acq`` tag for ``dwis``, instead of either one or the other.
* BUG FIX: The ``participants.tsv`` is correctly written to file.
* BUG FIX: Added functionality to obtain the acqusition date and time for source data.
* BUG FIX: Dropped unfilled BIDS metadata fields to avoid validation errors.
* BUG FIX: Fixed output ``scans.tsv`` files to include all the necessary information to pass BIDS validation.

0.2.0a5
---------

This version is an alpha release that contains two bug fixes.

* BUG FIX: Fixed bug in which strings/numbers were not converted to ``floats/ints``.

0.2.0a4
---------

This version is an alpha release that contains two bug fixes.

* BUG FIX: Fixed bug in which loading of ``NIFTI`` images to obtain information may throw errors.
* BUG FIX: Added better support for iterating and searching through nested dictionary of ``BIDS`` related terms.

0.2.0a3
---------

This version is an alpha release that contains a bug fix.

BUG FIX: Fixed issue that caused referenced to a ``dictionary`` rather than ``string``.

0.2.0a2
---------

This version is an alpha release that contains a bug fix.

BUG FIX: Uncaught ``OperationalError`` exception caused issues with intial queries in the ``sqlite`` database.

0.2.0a1
---------

This version is an alpha release that contains a bug fix.

BUG FIX: Executable scripts were not added on package install.

0.2.0a0
---------

This version is an alpha release that contains a bug fix, and substantial improvements and updates.

* BUG FIX: Fixed bug in which a DICOM file of the same series would be converted as separate acquisitions.
* UPDATE: Writes BIDS directory related files, such as the: ``README``, ``dataset_description.json``, and ``.bidsignore`` files.
* UPDATE: Optionally writes the ``participants.tsv`` and each subject's ``scans.tsv``.
* UPDATE: Utilizes a database to keep track of which source files have already been processed to avoid converting data that has already been processed.
* UPDATE: New functionality that symbolically links each subject's directory to the desired directory structure that ``convert_source`` requires. This allows for mapping a subject's study ID to their BIDS subject ID if these are different.
* UPDATE: Added wait bar to command line interface.
* UPDATE: Added function and executable to rename unknown scans.

v0.1.1
---------

* BUG FIX: Fixed issue for incorrect references to tmp directories. This caused image conversion exceptions to be thrown, and thus no NIFTI BIDS files would be returned.
* BUG FIX: Fixed issue for cases in which hidden indexing files (._) would be included in the file search.

v0.1.0
---------

* BUG FIX: Fixed bug in setup, which prevented proper installation and usage of the ``study_proc`` executable.
* UPDATE: The documentation is now `available <https://convert-source.readthedocs.io/en/0.1.0/>`_.

v0.1.rc1
---------

* Includes ``setup.py`` file, in addition to be published on PyPI.
* Much improved documentation.

v0.1.rc1a
--------------

Version: ``0.1 - release candidate 1 - alpha``

Substantial upgrades for ease of use. The parent study image directory and the output directory need to be provided as inputs.

The specified upgrades include:

* Specifying fewer command line parameters.
* Writes BIDS compatible JSON files for custom parameters and metadata.
* Allows for the option of NOT creating a sessions directory for each subject.
* Subject ID's DO NOT need to be specified on the command line.

v0.0.2
-------

This release has the bug fix for the error in which the script would not run without the exclusion file.

This version does not include a ``setup.py`` file and requires ``dcm2niix`` to be installed and added to path.
``FSL`` dependencies were removed and this version now uses ``nibabel`` for NIFTI file related functions. This current version is supported for MacOS, Linux, and, Windows platforms.

.. note:: ``nifti`` renaming functions are still under active development and are not implemented in this release.

v0.0.1
-------

This version does not include a ``setup.py`` file and requires ``dcm2niix`` to be installed and added to path. The bash wrapper script requires GNU parallel to run. Several bugs are still present at the moment of this initial release. This current version is only supported for MacOS and Linux. Later plans involve support for Windows.