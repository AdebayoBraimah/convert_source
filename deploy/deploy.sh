#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# TODO:
#   * [ ] Finish scripting the deployment process

# Commands for deploying a package to PyPI

# Markdown badges
# 
# https://github.com/Naereen/badges

# pip install twine
# rm -rf build .eggs *.egg* dist

python setup.py sdist bdist_wheel

# Test
twine check dist/*
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Upload/deploy
twine upload dist/*

# Testing env
# conda create --name test1 python=3 
# conda activate test1
# conda remove --name test1 --all

# curl https://bootstrap.pypa.io/get-pip.py | python
# pip install --upgrade setuptools

if [[ ${package_dir}/build ]]; then
    cd ${package_dir}
    rm -rf build .eggs *.egg* dist
    cd ${cwd}
fi

cd ${package_dir}

python setup.py sdist bdist_wheel

if [[ "${check_dist}" = "true" ]]; then
    twine check dist/*
fi

if [[ "${test_dist}" = "true" ]]; then
    twine upload dist/*
fi
