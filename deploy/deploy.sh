#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 
# Deploys python package to PyPI.

#######################################
# NOTES                               #
#######################################
#
# TODO                      
#   * [ ] Finish scripting the deployment process
#
# Commands for deploying a package to PyPI
#
# Markdown badges
#   * https://github.com/Naereen/badges

#######################################
# DEFINE FUNCTION(S)                  #
#######################################

#######################################
# Usage function. Prints help and then
#   exits.
# 
# Globals:
#   None
# 
# Arguments:
#   None
# 
# Outputs:
#   Usage - then exits.
#######################################
function Usage() {
  cat << USAGE

    Usage: $(basename ${0}) --setup-file setup.py [options]

  Deploys/uploads a python package/module to the Python Package Index (PyPI).

  Required argument:
    -s, --setup-file    Python setup file.

  Optional arguments:
    --check-dist        Check whether distribution’s long description will 
                          render correctly on PyPI [RECOMMENDED].
    --test-dist         Perform a test upload to Test PyPI.
    --no-clean-up       Clean-up the specified parent test directory [False].
    -h, -help, --help   Prints this help menu, and then exits.

    Usage: $(basename ${0}) --setup-file setup.py [options]

USAGE
  exit 1
}

#######################################
# Echoes status updates to the command 
#   line in some arbitrary color 
#   provided the ANSI escape codes:
#     * https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
# 
# Globals:
#   None
# 
# Arguments:
#   ansi_escape_code: ANSI escape code 
#     that corresponds to some color 
#     (e.g. '31m')
#   text: Text to echoed to the 
#     command line.
# 
# Outputs:
#   Text in some output color.
#######################################
function echo_color(){
  msg='\033[0;'"${@}"'\033[0m'
  echo -e ${msg} 
}

#######################################
# Echoes status updates to the command
#   in red.
# 
# Globals:
#   None
# 
# Arguments:
#   text: Text to echoed to the 
#     command line.
# 
# Outputs:
#   Text in red.
#######################################
function echo_red(){
  echo_color '31m'"${@}"
}

#######################################
# Echoes status updates to the command
#   in green.
# 
# Globals:
#   None
# 
# Arguments:
#   text: Text to echoed to the 
#     command line.
# 
# Outputs:
#   Text in green.
#######################################
function echo_green(){
  echo_color '32m'"${@}"
}

#######################################
# Echoes status updates to the command
#   in blue.
# 
# Globals:
#   None
# 
# Arguments:
#   text: Text to echoed to the 
#     command line.
# 
# Outputs:
#   Text in blue.
#######################################
function echo_blue(){
  echo_color '36m'"${@}"
}

#######################################
# Echoes status updates to the command
#   in red, and halts the script with 
#   an exit status of 1.
# 
# Globals:
#   None
# 
# Arguments:
#   text: Text to echoed to the 
#     command line.
# 
# Outputs:
#   Text in red, and Exit status of 1.
#######################################
function exit_error(){
  echo_red "${@}"
  exit 1
}

#######################################
# Dependency check function. Checks to 
#   see if the specified dependency is 
#   met (e.g. that the executable 
#   exists and is in the system path).
# 
# Globals:
#   None
# 
# Arguments:
#   cmd_exec: Dependency to be checked.
# 
# Outputs:
#   Exit status of 1 if the dependency 
#     is not met - None otherwise.
#######################################
function check_dependency() {
  cmd_exec=${1}

  if ! hash ${cmd_exec} 2>/dev/null; then
    exit_error "Dependency error: ${cmd_exec} is not installed."
  else
    echo_green "Required dependency met: ${cmd_exec}."
  fi
}

#######################################
# PARSE ARGUMENTS                     #
#######################################

# Set defaults
scripts_dir=$(realpath $(dirname ${0}))
cleanup=true
test_dist=false
cwd=$(pwd)

while [[ ${#} -gt 0 ]]; do
  case "${1}" in
    -s|--setup-file) shift; setup_file=${1} ;;
    --test-dist) test_dist=true ;;
    --check-dist) check_dist=true ;;
    --no-clean-up) cleanup=false ;;
    -h|-help|--help) Usage; ;;
    -*) echo ""; echo "$(basename ${0}): Unrecognized option ${1}" >&2; echo ""; Usage; ;;
    *) break ;;
  esac
  shift
done

#######################################
# CHECK ARGUMENT(S)                   #
#######################################

if [[ -z ${setup_file} ]] | [[ ! -f ${setup_file} ]]; then
  echo_red "\nPython setup file not provided or does not exist. See usage for help."
  Usage
else
  setup_file=$(realpath ${setup_file})
  package_dir=$(dirname ${setup_file})
fi

#######################################
# CHECK DEPENDENCIES                  #
#######################################

for depend in python twine; do
  check_dependency ${depend}
done

#######################################
# DEPLOY PACKAGE                      #
#######################################

cd ${package_dir}
python ${setup_file} sdist bdist_wheel

if [[ ${check_dist} = true ]]; then
  echo_blue "Performing check of the python package distrubtion long description."
  twine check dist/*
fi

if [[ ${test_dist} = true ]]; then
  echo_blue "Performing test upload."
  twine upload --repository-url https://test.pypi.org/legacy/ dist/*
else
  echo_blue "Performing upload to PyPI."
  twine upload dist/*
fi

cd ${cwd}

if [[ ${cleanup} = true ]]; then
  rm -rf build .eggs *.egg* dist
fi

# Old example code
# 
# Upgrade pip if needed
# curl https://bootstrap.pypa.io/get-pip.py | python
# pip install --upgrade setuptools
# 
# Testing env
# conda create --name test1 python=3 
# conda activate test1
# conda remove --name test1 --all
