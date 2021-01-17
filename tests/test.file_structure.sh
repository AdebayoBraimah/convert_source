#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# TO-DO:
# - Be sure to add gzip functionality to convert_source as gunzipped files
#     may introduce some variability.
# - Add option parser

# Define functions

#######################################
# Usage function. Prints help and then
# exits.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Usage - then exits.
#######################################
function Usage() {
  cat << USAGE

    Usage: $(basename ${0}) --out-dir <output_directory> [--clean-up]

  Creates temporary pre-determined test cases for directory structure and
  file layout for testing the file searching capabilities for the
  'convert_source' package.

  Required arguments:
    -o, --out-dir       Output parent directory for child test directories.

  Optional arguments:
    --clean-up          Clean-up the specified parent test directory [False].
    -h, -help, --help   Prints this help menu, and then exits.

    Usage: $(basename ${0}) --out-dir <output_directory> [--clean-up]

USAGE
  exit 1
}

#######################################
# Zero pads number/string with some
# arbitrary string and some arbitrary 
# number of zeroes.
# Globals:
#   None
# Arguments:
#   num_z: Number of zeroes to zero pad with.
#   num: Number or string to be zero padded.
# Outputs:
#   zero padded number/string
#######################################
function zero_pad(){

  num_z=${1}
  num=${2}

  echo $(printf %0${num_z}d ${num})
}

#
# Parse Command Line Variables
#========================================

# Set defaults
cleanup=false

while [[ ${#} -gt 0 ]]; do
  case "${1}" in
    -o|--out-dir) shift; outdir=${1} ;;
    --clean-up) cleanup=true ;;
    -h|-help|--help) Usage; ;;
    -*) echo ""; echo "$(basename ${0}): Unrecognized option ${1}" >&2; echo ""; Usage; ;;
    *) break ;;
  esac
  shift
done

#
# Option checks
#========================================

if [[ -z ${outdir} ]]; then
  echo ""; echo "REQUIRED: Output directory not specified. Exiting..." >&2; echo ""; # Usage;
  exit 1
elif [[ -d ${outdir} ]] && [[ ${cleanup} = "false" ]]; then
  echo ""; echo "ERROR: Output directory already exists. Exiting..."; echo ""
  exit 1
fi

# Define parent scripts directory
# scripts_dir=$(dirname ${0})
scripts_dir=$(pwd)

#
# Run-time checks
#========================================

if [[ ${cleanup} = "false" ]]; then
  # Test directory
  # test_dir=${scripts_dir}/img.test.dir
  test_dir=${outdir}

  if [[ ! -d ${test_dir} ]]; then
    mkdir -p ${test_dir}
  fi

  # subject arrays
  subs=( 
    001
    002
    003
    P01
    P02
    P03
    C01
    C02
    C03
  )

  # Create test directory file structure for PAR REC/NIFTI file(s)
  for sub in ${subs[@]}; do
    echo ""; echo "Processing: sub-${sub}"

    if [[ ! -d ${test_dir}/${sub}/NIFTI ]]; then
      mkdir -p ${test_dir}/${sub}/NIFTI
      mkdir -p "${test_dir}/${sub}/PAR REC"
    fi

    # Image array
    imgs=( T1 T2 FLAIR SWI rs-func task-1-func task-2-func rs-func_sbref task-func_sbref DWI_32dir DWI_68dir DWI_sbref )

    # Image directories for NIFTI/PAR REC data
    for img in ${imgs[@]}; do
      touch ${test_dir}/${sub}/NIFTI/${img}.nii.gz
      touch "${test_dir}/${sub}/PAR REC/${img}.PAR"
      touch "${test_dir}/${sub}/PAR REC/${img}.REC"
    done

    # Create corresponding FSL bval/bvec files for NIFTI DWI
    touch ${test_dir}/${sub}/NIFTI/DWI_32dir.bval
    touch ${test_dir}/${sub}/NIFTI/DWI_32dir.bval

    touch ${test_dir}/${sub}/NIFTI/DWI_68dir.bval
    touch ${test_dir}/${sub}/NIFTI/DWI_68dir.bval

    # Image directories for DICOM data
    files=( $(seq 1 1 25) )

    for img in ${imgs[@]}; do
      if [[ ! -d ${test_dir}/${sub}/DICOM/20211701/${img} ]]; then
        mkdir -p ${test_dir}/${sub}/DICOM/20211701/${img}
      fi
      for file in ${files[@]}; do
        touch ${test_dir}/${sub}/DICOM/20211701/${img}/$(zero_pad 8 ${file}).dcm
      done
    done
  done

  # Edge raw data directory layout cases 
  # subject arrays
  subs=( 
    900XXT5
    901XXP5
    902XXY8
  )

  for sub in ${subs[@]}; do
    echo ""; echo "Processing: sub-${sub}"

    if [[ ! -d ${test_dir}/${sub}/NIFTI ]]; then
      mkdir -p "${test_dir}/${sub}/NIFTI/NAME^ 20201701"
      mkdir -p "${test_dir}/${sub}/PAR REC/NAME^ 20201701"
    fi

    # Image array
    imgs=( T1 T2 FLAIR SWI rs-func task-1-func task-2-func rs-func_sbref task-func_sbref DWI_32dir DWI_68dir DWI_sbref )

    # Image directories for NIFTI/PAR REC data
    for img in ${imgs[@]}; do
      touch "${test_dir}/${sub}/NIFTI/NAME^ 20201701/${img}.nii.gz"
      touch "${test_dir}/${sub}/PAR REC/NAME^ 20201701/${img}.PAR"
      touch "${test_dir}/${sub}/PAR REC/NAME^ 20201701/${img}.REC"
    done

    # Create corresponding FSL bval/bvec files for NIFTI DWI
    touch "${test_dir}/${sub}/NIFTI/NAME^ 20201701/DWI_32dir.bval"
    touch "${test_dir}/${sub}/NIFTI/NAME^ 20201701/DWI_32dir.bval"

    touch "${test_dir}/${sub}/NIFTI/NAME^ 20201701/DWI_68dir.bval"
    touch "${test_dir}/${sub}/NIFTI/NAME^ 20201701/DWI_68dir.bval"

    # Image directories for DICOM data
    files=( $(seq 1 1 25) )

    for img in ${imgs[@]}; do
      if [[ ! -d "${test_dir}/${sub}/DICOM/20211701/NAME^ 20201701/${img}" ]]; then
        mkdir -p "${test_dir}/${sub}/DICOM/20211701/NAME^ 20201701/${img}"
      fi
      for file in ${files[@]}; do
        touch "${test_dir}/${sub}/DICOM/20211701/NAME^ 20201701/${img}/$(zero_pad 8 ${file}).dcm"
      done
    done
  done
elif [[ ${cleanup} = "true" ]] && [[ -d ${outdir} ]]; then
  echo ""; echo "Performing clean-up"
  rm -rf ${outdir}
fi

echo ""
echo "Done"
echo ""

