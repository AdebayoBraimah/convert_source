#!/usr/bin/env bash

cwd=$(pwd)

wd=$(dirname ${0})
wd=$(pwd)

# echo ${wd}
# pip install sphinx sphinx-autodoc-typehints sphinx_rtd_theme sphinx-autodoc-napoleon-typehints sphinx-argparse

# sphinx-quickstart
# sphinx-apidoc -o source ../convert_source

# make clean
# make html

sphinx-apidoc -o source ../../convert_source; make clean; make html

cd ${cwd}

# This is for github pages
# 
# copy source directory to docs, update conf.py
# 
# cp -r build/html/* ../../docs
# touch ../../docs/.nojekyll
# rm -rf build
