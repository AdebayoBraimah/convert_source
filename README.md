# convert_source
Convert source DICOM or PAR REC image data to BIDS directory layout.

The YAML configuration file used as input dictates the search terms used to find and rename files. Please see `config.default.yml` as an example.

Requires `dcm2niix` and `pydicom` in addition to `FSL` (FMRIB Software Library).

```
usage: convert_source.py [-h] -s subject_ID -o Output_BIDS_Directory -d
                         data_directory -c config.yml -f file_type
                         [-ses session] [-k] [-v] [-version]

Performs conversion of source DICOM, PAR REC, and Nifti data to BIDS directory
layout. convert_source v1.0.0

optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  -s subject_ID, -sub subject_ID, --sub subject_ID
                        Unique subject identifier given to each participant.
                        This indentifier CAN contain letters and numbers. This
                        identifier CANNOT contain: underscores, hyphens,
                        colons, semi-colons, spaces, or any other special
                        characters.
  -o Output_BIDS_Directory, -out Output_BIDS_Directory, --out Output_BIDS_Directory
                        BIDS output directory. This directory does not need to
                        exist at runtime. The resulting directory will be
                        populated with BIDS named and structured data.
  -d data_directory, -data data_directory, --data data_directory
                        Parent directory that contains that subuject's
                        unconverted source data. This directory can contain
                        either all the PAR REC files, or all the directories
                        of the DICOM files. NOTE: filepaths with spaces either
                        need to replaced with underscores or placed in quotes.
                        NOTE: The PAR REC directory is rename PAR_REC
                        automaticaly.
  -c config.yml, -config config.yml, --config config.yml
                        YAML configuruation file that contains modality
                        search, parameters, metadata, and exclusion list.
  -f file_type, -file file_type, --file-type file_type
                        File type that is to be used with the converter.
                        Acceptable choices include: DCM, PAR, or, NII.

Optional arguments:
  -ses session, --ses session
                        Session label for the acquired source data. [default:
                        1]
  -k, -keep, --keep-unknown
                        Keep or remove unknown modalities [default: True].
  -v, -verbose, --verbose
                        Prints additional information to screen. [default:
                        False]
  -version, --version   Prints version to screen and exits. convert_source
                        v1.0.0
```
