[![CircleCI](https://circleci.com/gh/AdebayoBraimah/convert_source.svg?style=svg)](https://app.circleci.com/pipelines/github/AdebayoBraimah/convert_source) [![Documentation Status](https://readthedocs.org/projects/convert-source/badge/?version=latest)](https://convert-source.readthedocs.io/en/latest/)

# convert_source
Convert source `DICOM`, `PAR REC` or `NIFTI` image data to BIDS directory layout.

The YAML configuration file used as input dictates the search terms used to find and rename files. Please see `config/config.default.yml` or `config/config.example.yml` for examples.

Requires `dcm2niix` and `pydicom`.

```
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
```
