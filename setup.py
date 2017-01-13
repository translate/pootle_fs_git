# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Pootle filesystem plugins
"""

import re

from distutils import log

# Always prefer setuptools over distutils
from setuptools import setup, find_packages


def parse_requirements(file_name, recurse=False):
    """Parses a pip requirements file and returns a list of packages.

    Use the result of this function in the ``install_requires`` field.
    Copied from cburgmer/pdfserver.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        # Ignore comments, blank lines and included requirements files
        if re.match(r'(\s*#)|(\s*$)|'
                    '((--allow-external|--allow-unverified) .*$)', line):
            continue
        if re.match(r'-r .*$', line):
            if recurse:
                requirements.extend(parse_requirements(
                    'requirements/' +
                    re.sub(r'-r\s*(.*[.]txt)$', r'\1', line), recurse))
            continue

        if re.match(r'^\s*-e\s+', line):
            requirements.append(re.sub(
                r'''\s*-e\s+          # -e marker
                 .*                   # URL
                 \#egg=               # egg marker
                 ([^\d]*)-            # \1 dep name
                 ([\.\d]*             # \2 M.N.*
                 ((a|b|rc|dev)+\d*)*  # (optional) devN
                 )$''',
                r'\1==\2', line, flags=re.VERBOSE))
            log.warn("Pootle requires a non-PyPI dependency, when using pip "
                     "ensure you use the --process-dependency-links option.")
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements

install_requires = parse_requirements('requirements/base.txt')

setup(
    name='pootle_fs_git',
    version='0.0.1',
    description='Pootle file system plugins',
    long_description="Integration between Pootle and FS backends",
    url='https://github.com/phlax/pootle_fs_git',
    author='Ryan Northey',
    author_email='ryan@synca.io',
    license='GPL3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GPL3',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='pootle filesystem plugins',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=install_requires,
)
