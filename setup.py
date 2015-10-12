#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2013 Translate House
#
# This file is part of pootle_fs_git.
#
# pootle_fs_git is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# pootle_fs_git is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pootle_fs_git; if not, see <http://www.gnu.org/licenses/>.

"""Pootle filesystem plugins
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

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
    install_requires=['pootle_fs', "gitpython"],
)
