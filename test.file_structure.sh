#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# TO-DO:
# - Be sure to add gzip functionality to convert_source as gunzipped files
#     may introduce some variability.

# Define functions

# Zero pads number/string with some
# arbitrary string and some arbitrary 
# number of zeroes.
function zero_pad(){

    num_z=${1}
    num=${2}

    echo $(printf %0${num_z}d ${num})
}

# Define parent scripts directory
# scripts_dir=$(dirname ${0})
scripts_dir=$(pwd)

# Test directory
test_dir=${scripts_dir}/img.test.dir

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
    echo ""
    echo "Processing: sub-${sub}"

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
    echo ""
    echo "Processing: sub-${sub}"

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

echo ""
echo "Done"
echo ""

