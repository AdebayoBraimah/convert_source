#!/usr/bin/env bash
# 
# -*- coding: utf-8 -*-
# title           : source2BIDS.sh
# description     : [description]
# author          : Adebayo B. Braimah
# e-mail          : adebayo.braimah@cchmc.org
# date            : 2019 09 27 12:15:24
# version         : 0.2.0
# usage           : source2BIDS.sh [-h,--help]
# notes           : [notes]
# bash_version    : 5.0.7
#==============================================================================

#
# Define Usage & (Miscellaneous) Function(s)
#==============================================================================

Usage() {
  cat << USAGE

  Usage: $(basename ${0}) [options] -f <file_list.txt> -s <sub_list.txt> -P [options]

This is a wrapper for a python script that performs source data conversion from either
PAR REC or DICOM to BIDS NifTi. This script is intended for the IRC 287H and 317H 
Neonatal studies and their corresponding imaging protocol(s).

Dependencies include working installations of:

- dcm2niix (DICOM to nifti, preferably after 2019 April)
- Python3
  - pandas  - scipy
  - pydicom - pyyaml

Compulsory Inputs:

-f,-file,--file-list    Text file that contains the absolute paths to the PAR REC or parent DICOM directory for each subject.
-s,-sub,--sub-list      Text file that contains the subject ID for the corresponding PAR REC or parent DICOM directory.
-P,--PAR                Indicates that PAR REC files are to be converted
-D,--DCM                Indicates that DICOM files are to be converted

Optional Inputs:

-ses,--ses              Session ID for the study. [Default: 1]
-o,-out,--output-dir    Output directory for the converted files. This directory will contain the 'rawdata' subdirectory. [Default: current working directory]
-c,--config             Exclusion configuration YAML file.
-v,--verbose            Prints output to the command line. [Default: disabled]
-vL,--verbose-logging   Prints verbose logs to the 'ConvLogs' subdirectory within the output directory. [Default: disabled]

----------------------------------------

-h,-help,--help 		Prints usage and exits.

NOTE: 
- '--PAR' and '--DCM' options are mutually exclusive.
  Should both types of files be present for the same subject, 
  then this script must be run twice, specifying the file type.
- Requires GNU Parallel to run.
  - Conversion not available in parallel (yet...), but
    used as the case of filenames with spaces are handled
    much better than from the regular commands.
- '--PAR' option renames filepaths that contain the space
  in "PAR REC" file paths.

----------------------------------------

Adebayo B. Braimah - 2019 09 27 12:15:24

$(basename ${0}) v0.2.0

----------------------------------------

  Usage: $(basename ${0}) [options] -f <file_list.txt> -s <sub_list.txt> -P 

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
  eval ${@} >> ${log} 2>> ${err}
  if [ ! ${?} -eq 0 ]; then
    exit_error "${@} : command failed, see error log file for details: ${err}"
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
# Parse Command Line Variables
#==============================================================================

# Run time switches native to bash
# set -e # exit if error
# set -x # for verbose printing/debugging
scriptsDir=$(dirname $(realpath ${0}))

# Set Defaults
outDir=""
config=${scriptsDir}/convExclude.yml
ses=1
par=false
dcm=false

# Parse options
while [ ${#} -gt 0 ]; do
  case "${1}" in
    -f|-file|--file-list) shift; fileList=${1} ;;
    -s|-sub|--sub-list) shift; subList=${1} ;;
    -ses|--ses) shift; ses=${1} ;;
    -o|-out|--output-dir) shift; outDir=${1} ;;
    -c|--config) shift; config=${1} ;;
    -P|--PAR) par=true ;;
    -D|--DCM) dcm=true ;;
    -v|--verbose) verbose=true ;;
    -vL|--verbose-logging) vL=true ;;
    -h|-help|--help) Usage; ;;
    -*) echo_red "$(basename ${0}): Unrecognized option ${1}" >&2; Usage; ;;
    *) break ;;
  esac
  shift
done

#
# Verify Essential Arguments & Get Absolute Paths
#==============================================================================

# Required Arguments
if [[ ! -f ${fileList} ]] || [[ -z ${fileList} ]]; then
  echo_red "Required: File list text file not passed as an argument or does not exist. Please check."
  # run echo "Required: File list text file not passed as an argument or does not exist. Please check"
  exit 1
else
  fileList=$(realpath ${fileList})
fi

if [[ ! -f ${subList} ]] || [[ -z ${subList} ]]; then
  echo_red "Required: Subject list text file not passed as an argument or does not exist. Please check."
  # run echo "Required: Subject list text file not passed as an argument or does not exist. Please check."
  exit 1
else
  subList=$(realpath ${subList})
fi

if [[ ${par} = "false" ]] && [[ ${dcm} = "false" ]]; then
  echo_red "Required: Source data format must be specified as either: '--PAR' for PAR REC files or '--DCM' for DICOM files."
  exit 1
elif [[ ${par} = "true" ]] && [[ ${dcm} = "true" ]]; then
  echo_red "'--PAR' and '--DCM' are mutually exclusive options. Please pick one."
  exit 1
elif [[ ${par} = "true" ]]; then
  type=PAR
elif [[ ${dcm} = "true" ]]; then
  type=DCM
fi

# Optional Arguments
if [[ -z ${outDir} ]]; then
  outDir=$(pwd)
elif [ ! -z ${outDir} ]; then
  outDir=$(realpath ${outDir})
fi

if [[ -z ${ses} ]]; then
  echo_red "Session ID was not passed as an argument but not specified. Please check."
fi

if [[ ! -f ${config} ]] || [[ -z ${config} ]]; then
  echo_red "YAML configuration file was not passed as an argument or does not exist. Please check."
  # run echo "Topup configuration file was not passed as an argument or does not exist. Please check."
  exit 1
else
  config=$(realpath ${config})
fi

#
# Read in text file data
#==============================================================================

mapfile -t subs < ${subList}
mapfile -t files < ${fileList}

outBIDS=${outDir}/rawdata
# outBIDS=${outDir}

#
# Make the Necessary Directories
#==============================================================================

if [[ ${vL} = "true" ]]; then
  logDir=${outDir}/ConvLogs
  mkdir -p ${logDir}
fi

#
# Perform Source Data Converstion of BIDS NifTi
#==============================================================================

# Iterate through each subject
for ((i = 0; i < ${#subs[@]}; i++)); do
  # Set base command
  cmd="${scriptsDir}/convertSource.py --sub ${subs[$i]} --out ${outBIDS} --data \"${files[$i]}\" --filetype ${type} --ses ${ses}"

  # append config file if provided
  if [[ ! -z ${config} ]]; then
    cmd+=" --exclude ${config}"
  fi

  # Add verbosity level to command
  if [[ ${verbose} = "true" ]] && [[ ${vL} = "true" ]]; then
    cmd+=" --verbose>>${logDir}/sub-${subs[$i]}-ses-00${ses}_convLog.txt"
  elif [[ ${vL} = "true" ]]; then
    cmd+=" --verbose>>${logDir}/sub-${subs[$i]}-ses-00${ses}_convLog.txt"
  elif [[ ${verbose} = "true" ]]; then
    cmd+=" --verbose"
  fi

  # Execute command
  # ${cmd}

  # Print command to file
  echo "${cmd}">>${logDir}/convCmds.txt
  
  # Clear cmd variable
  unset cmd
done

parallel --jobs=1 < ${logDir}/convCmds.txt
