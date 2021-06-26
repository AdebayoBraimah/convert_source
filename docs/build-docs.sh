#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 
# Build documentation using Sphinx.

#######################################
# NOTES                               #
#######################################
# 
# Commands for building restructered 
#   text and html documentation for a
#   python module/package.
# 
# Google style guide:
#   * https://google.github.io/styleguide/shellguide.html
# 
# For hosting on GitHub Pages
# 
#   * Copy source directory to docs, update conf.py
#       cp -r build/html/* ../../docs
#       touch ../../docs/.nojekyll
#       rm -rf build


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

    Usage: $(basename ${0}) [--sphinx-quickstart | --build-docs] [options]

  Builds documentation for a python module/package. Mainly intended for locally building and inspecting documentation prior to hosting 
  elsewhere.

  Quickstart options:

    -q, --quickstart, --sphinx-quickstart   Activates sphinx-quickstart to quickly build a configuration file for documentaiton building.
    -d, --docs-dir                          The output directory for documentation related files to be placed.

  Documention building options:

    -b, --build-docs                        Activates sphinx-apidoc to build documentation [NOTE: This requires an existing 
                                            documentation directory].
    -s, --source                            Path to source directory that contains the configuration file, in addition to the 
                                            reStructuredText (.rst) files.
    -p, --package                           Path to package directory.

  Optional arguments:
    -h,-help,--help                         Prints the help menu

  NOTE:
    * This script assumes separate source and build directories when building documentation.
    * Although not required, '--sphinx-quickstart' should be specified with separate build and source files directories.
    * If module documentation needs to be updated, then it must be regenerated. This can be accomplished by removing the module document
      in question, and then running this script using the '--build-docs' option.
    * Should the generated documents need to be hosted elsewhere (e.g. GitHub, or ReadTheDocs), then the build directory should be 
      removed.
    * These modules/packages are required and must be installed via pip prior to running this script:
        * sphinx            * sphinx-autodoc-typehints 
        * sphinx_rtd_theme  * sphinx-argparse
  

    Usage: $(basename ${0}) [--sphinx-quickstart | --build-docs] [options]

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
cwd=$(pwd)
quickstart=false
build_docs=false

cleanup=true
cwd=$(pwd)

while [[ ${#} -gt 0 ]]; do
  case "${1}" in
    -q|--quickstart|--sphinx-quickstart) quickstart=true ;;
    -b|--build-docs) build_docs=true ;;
    -d|--docs-dir) shift; docs_dir=${1} ;;
    -s|--source) shift; source_dir=${1} ;;
    -p|--package) shift; package_dir=${1} ;;
    -h|-help|--help) Usage; ;;
    -*) echo ""; echo "$(basename ${0}): Unrecognized option ${1}" >&2; echo ""; Usage; ;;
    *) break ;;
  esac
  shift
done


# cwd=$(pwd)

# wd=$(dirname ${0})
# wd=$(pwd)

# echo ${wd}
# pip install sphinx sphinx-autodoc-typehints sphinx_rtd_theme sphinx-autodoc-napoleon-typehints sphinx-argparse

# sphinx-quickstart
# sphinx-apidoc -o source ../convert_source

# make clean
# make html

# sphinx-apidoc -o source ../../convert_source; make clean; make html

# cd ${cwd}

# This is for github pages
# 
# copy source directory to docs, update conf.py
# 
# cp -r build/html/* ../../docs
# touch ../../docs/.nojekyll
# rm -rf build

#######################################
# CHECK DEPENDENCIES                  #
#######################################

for depend in make python; do
  check_dependency ${depend}
done

#######################################
# CHECK ARGUMENT(S)                   #
#######################################

# Check mutually exclusive options
if [[ ${quickstart} = true ]] && [[ ${build_docs} = true ]]; then
  echo_red "Both '--sphinx-quickstart' and '--build-docs' cannot be specified."
  Usage
elif [[ ${quickstart} = false ]] && [[ ${build_docs} = false ]]; then
  echo_red "Either '--sphinx-quickstart' or '--build-docs' must be specified."
  Usage
fi

# Check quickstart specific options
if [[ ${quickstart} = true ]]; then
  if [[ -z ${docs_dir} ]]; then
    echo_red "'--docs-dir' must be specified with the '--sphinx-quickstart' option."
    Usage
  fi
fi

# Check build_docs specific options
if [[ ${build_docs} = true ]]; then
  # Check source directory
  if [[ -z ${source_dir} ]] || [[ ! -d ${source_dir} ]]; then
    echo_red "'--source' must be specified with the '--build-docs' option."
    Usage
  else
    source_dir=$(realpath ${source_dir})
  fi

  # Check package directory
  if [[ -z ${package_dir} ]] || [[ ! -d ${package_dir} ]]; then
    echo_red "'--package' must be specified with the '--build-docs' option."
    Usage
  else
    package_dir=$(realpath ${package_dir})
  fi
fi

#######################################
# QUICK START DOCS SETUP              #
#######################################

if [[ ${quickstart} = true ]]; then
  if [[ ! -d ${docs_dir} ]]; then
    echo_blue "Making documentaiton directory."
    mkdir -p ${docs_dir}
  fi

  cd ${docs_dir}
  sphinx-quickstart
  echo_green "Done!"
fi

#######################################
# BUILD DOCS                          #
#######################################

if [[ ${build_docs} = true ]]; then
  cd $(dirname ${source_dir})
  sphinx-apidoc --output-dir=${source_dir} ${package_dir}; make clean; make html
  cd ${cwd}
  echo_green "Done!"
fi
