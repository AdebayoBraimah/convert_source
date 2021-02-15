CHANGES
=========

v0.1.0
---------

* BUG FIX: Fixed bug in setup, which prevented proper installation and usage of the ``study_proc`` executable.
* UPDATE: The documentation is now `available <https://convert-source.readthedocs.io/en/master/>`_.

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