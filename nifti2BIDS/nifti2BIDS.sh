#!/usr/bin/env bash
# 
# -*- coding: utf-8 -*-
# title           : nifti2BIDS.sh
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2019 08 20 09:36:37
# version         : 0.0.1
# usage           : nifti2BIDS.sh [-h,--help]
# notes           : [notes]
# bash_version    : 5.0.7
#==============================================================================

#
# Define Usage & (Miscellaneous) Function(s)
#==============================================================================

Usage() {
  cat << USAGE

  Usage: $(basename ${0}) --data <NIFTI_files_directory> --out <output_directory> --sub 001 --ses 1

Copies files already converted from raw image data
by the (Philips) Scanner and renames it to
be consistent with the BIDS naming convention.

The keywords used to search (via globbing) are
consistent with the naming convention used for 
the neonatal neuroimaging protocols (IRC287 and IRC317).

---- 

Compulsory inputs are:

-d,-data,--data     Directory that contains that subject's nifti files.
-o,-out,--out       Output (parent) BIDS directory. Most likely RawData if the nifti files are contained in SourceData.
-s,-sub,--sub       Subject ID (must be the same as in the BIDS directory).

Optional inputs:

-ses,--ses          Session number [Default: 1]

----------------------------------------

-h,-help,--help 		Prints usage and exits.

NOTE: 

----------------------------------------

Adebayo B. Braimah - 2019 08 20 15:36:37

----------------------------------------

  Usage: $(basename ${0}) -d <NIFTI_files_directory> -o <output_directory> -s 001 

USAGE
  exit 1
}

#
# Define Logging Function(s)
#==============================================================================

# Echoes status updates to the command line
echo_color(){
  msg='\033[0;'"${@}"'\033[0m'
  # echo -e ${msg} >> ${stdOut} 2>> ${stdErr}
  echo -e ${msg} 
}
echo_red(){
  echo_color '31m'"${@}"
}
echo_green(){
  echo_color '32m'"${@}"
}
echo_blue(){
  echo_color '36m'"${@}"
}

exit_error(){
  echo_red "${@}"
  exit 1
}

# Run and log the command
run_cmd(){
  # stdOut=${outDir}/LogFile.txt
  # stdErr=${outDir}/ErrLog.txt
  echo_blue "${@}"
  eval ${@} >> ${stdOut} 2>> ${stdErr}
  if [ ! ${?} -eq 0 ]; then
    exit_error "${@} : command failed, see error log file for details: ${stdErr}"
  fi
}

# log function for completion
run()
{
  # log=${outDir}/LogFile.txt
  # err=${outDir}/ErrLog.txt
  echo "${@}"
  "${@}" >>${log} 2>>${err}
  if [ ! ${?} -eq 0 ]; then
    echo "failed: see log files ${log} ${err} for details"
    exit 1
  fi
  echo "-----------------------"
}

if [ ${#} -lt 1 ]; then
  Usage >&2
  exit 1
fi

#
# Parse Options and Set Variables/Defaults
#==============================================================================

# Run time switches native to bash
# set -e # exit if error
# set -x # for verbose printing/debugging
scriptsDir=$(dirname $(realpath ${0}))

# Set Defaults
ses=1

# Parse options
while [ ${#} -gt 0 ]; do
  case "${1}" in
    -s|-sub|--sub) shift; sub=${1} ;;
    -o|-out|--out) shift; outDir=${1} ;;
    -d|-data|--data) shift; dataDir=${1} ;;
    -ses|--ses) shift; ses=${1} ;;
    -h|-help|--help) Usage; ;;
    -*) exit_error "${0}: Unrecognized option ${1}" >&2; Usage; ;;
    *) break ;;
  esac
  shift
done

#
# Define Helper Functions
#==============================================================================

runNum(){ 

  # Gets the number of runs
  # in a directory and 
  # returns the N+1 number.

  local outDir=${1}
  local mod=${2}
  local task=${3}
  local acq=${4}
  local scan=${5}
  local ses=${6}

  ses="ses-$(zeropad ${ses} 3)"
  out=${outDir}/${ses}

  runNumber=""

  a=( $(ls ${out}/${mod}/*${task}*${acq}*${scan}*.nii*) )
  runNumber=${#a[@]}
  runNumber=$((${runNumber}+1))
  runNumber=$(zeropad ${runNumber} 2)
  echo ${runNumber}
}

numFrame(){

  # Gets the number of 
  # frames in a nifti 
  # file.

  local niiFile=${1}

  frameNum=$(fslval ${niiFile} dim4)
  echo ${frameNum}
}

# Example command
# 
# /Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/nifti2BIDS/nifti2BIDS.sh \
# -o /Volumes/brac4g/IRC317H/BIDS/RawData \
# -s C09 -d /Volumes/brac4g/IRC317H/BIDS/SourceData/IRC317H-C9/NIFTI 

#
# Copy and Rename (Scanner) NifTi Files to BIDS Format
#==============================================================================

echo_blue "Processing: sub-${sub}\n"  
files=( $(ls ${dataDir}/*.nii*) )

for file in ${files[@]}; do
  out=${outDir}/sub-${sub}
  ses=${ses}
  if [[ ${file} == *"Vis"* ]]; then
    mod=func
    task="visualstrobe"

    numFrame=$(numFrame ${file})
    if [ ${numFrame} -eq 1 ]; then
      acq=AP
      scan="sbref"
      runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
      outName=sub-${sub}_ses-$(zeropad ${ses} 3)_task-${task}_acq-${acq}_run-${runNumber}_${scan}
      cp ${file} ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      gzip ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      cp ${scriptsDir}/template_func_rest_sbref.json ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.json
    else
      acq=PA
      scan="bold"
      runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
      outName=sub-${sub}_ses-$(zeropad ${ses} 3)_task-${task}_acq-${acq}_run-${runNumber}_${scan}
      cp ${file} ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      gzip ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      cp ${scriptsDir}/template_func_visualstrobe_bold.json ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.json
    fi
  elif [[ ${file} == *"rsfMR"* ]]; then
    mod=func
    task="rest"

    numFrame=$(numFrame ${file})
    if [ ${numFrame} -eq 1 ]; then
      acq=AP
      scan="sbref"
      runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
      outName=sub-${sub}_ses-$(zeropad ${ses} 3)_task-${task}_acq-${acq}_run-${runNumber}_${scan}
      cp ${file} ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      gzip ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      cp ${scriptsDir}/template_func_rest_sbref.json ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.json
    else
      acq=PA
      scan="bold"
      runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
      outName=sub-${sub}_ses-$(zeropad ${ses} 3)_task-${task}_acq-${acq}_run-${runNumber}_${scan}
      cp ${file} ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      gzip ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.nii
      cp ${scriptsDir}/template_func_rest_bold.json ${out}/ses-$(zeropad ${ses} 3)/func/${outName}.json
    fi
  elif [[ ${file} == *"T1"* ]]; then
    mod=anat
    task=""
    scan="T1w"
    acq=""

    # runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
    runNumber=$(runNum ${out} ${mod} "" "" ${scan} ${ses})
    outName=sub-${sub}_ses-$(zeropad ${ses} 3)_run-${runNumber}_${scan}
    cp ${file} ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.nii
    gzip ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.nii
    cp ${scriptsDir}/template_anat_T1w.json ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.json
  elif [[ ${file} == *"T2"* ]]; then
    mod=anat
    task=""
    scan="T2w"
    acq=""

    # runNumber=$(runNum ${out} ${mod} ${task} ${acq} ${scan} ${ses})
    runNumber=$(runNum ${out} ${mod} "" "" ${scan} ${ses})
    outName=sub-${sub}_ses-$(zeropad ${ses} 3)_run-${runNumber}_${scan}
    cp ${file} ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.nii
    gzip ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.nii
    cp ${scriptsDir}/template_anat_T2w.json ${out}/ses-$(zeropad ${ses} 3)/anat/${outName}.json
  fi
done

