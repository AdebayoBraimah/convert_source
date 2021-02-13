
pip install sphinx
pip install sphinx-autodoc-typehints

sphinx-apidoc -o source ../convert_source

make clean

make html
