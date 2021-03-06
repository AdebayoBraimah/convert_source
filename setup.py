from os import path
from setuptools import setup, find_packages

# Read the version from file
with open(path.join(path.dirname(__file__), 'version.txt')) as fid:
    version = fid.read().strip()

# Read the contents of the README file
with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as fid:
    readme = fid.read()

# Read the contents of the requirements file
with open(path.join(path.abspath(path.dirname(__file__)), 'requirements.txt')) as fid:
    requirements = fid.read().splitlines()

setup(name                           = 'convert_source',    # Required
      version                        = version,             # Required
      packages                       = find_packages(),     # Required
      install_requires               = requirements,
      python_requires                = '>=3.6',
      setup_requires                 = ["pytest-runner"],
      tests_require                  = ["pytest", "pytest-cov", "coverage"],
      classifiers                    = ['Programming Language :: Python :: 3',
                                        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                                        'Operating System :: OS Independent'],
      keywords                       = 'bids mri imaging neuroimaging dicom par rec nifti',
      description                    = 'Converts and organises source MR image data-sets in accordance with the Brain Imaging Data Structure (BIDS)',
      long_description               = readme,
      long_description_content_type  = 'text/markdown',
      author                         = 'Adebayo Braimah',
      author_email                   = 'adebayo.braimah@cchmc.org',
      url                            = 'https://github.com/AdebayoBraimah/convert_source')