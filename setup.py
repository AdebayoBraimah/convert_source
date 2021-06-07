from os import path
from setuptools import setup, find_packages

# Read the version from file
with open(path.join(path.dirname(__file__), 'convert_source', 'version.txt')) as fid:
    version = fid.read().strip()

# Read the contents of the README file
with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as fid:
    readme = fid.read()

# Read the contents of the requirements file
with open(path.join(path.abspath(path.dirname(__file__)), 'requirements.txt')) as fid:
    requirements = fid.read().splitlines()

setup(name                           = 'convert_source',                    # Required
      version                        = version,                             # Required
      packages                       = find_packages(exclude=['tests']),    # Required
      license                        = 'GPL-3.0 License',
      classifiers                    = ['Intended Audience :: Science/Research',
                                        'Natural Language :: English',
                                        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                                        'Operating System :: OS Independent',
                                        'Programming Language :: Python :: 3'],
      install_requires               = requirements,
      python_requires                = '>=3.7',
      scripts                        = ['convert_source/bin/study_proc',
                                        'convert_source/bin/prep_study',
                                        'convert_source/bin/unknown2bids'],
      setup_requires                 = ["pytest-runner"],
      tests_require                  = ["pytest", "pytest-cov", "coverage"],
      keywords                       = 'bids mri imaging neuroimaging dicom par rec nifti',
      description                    = 'Converts and organises source MR image data-sets in accordance with the Brain Imaging Data Structure (BIDS)',
      long_description               = readme,
      long_description_content_type  = 'text/markdown',
      author                         = 'Adebayo Braimah',
      author_email                   = 'adebayo.braimah@cchmc.org',
      include_package_data           = True,
      url                            = 'https://github.com/AdebayoBraimah/convert_source'
      # entry_points                   = {'console_scripts': ['study_proc=convert_source.bin.study_proc:main']}
      )