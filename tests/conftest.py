#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
import tempfile
from pkgutil import iter_modules

import pytest

from django import setup
from django.conf import settings

from . import fixtures


@pytest.fixture(autouse=True, scope='session')
def setup_db_if_needed(request, tests_use_db):
    """Sets up the site DB only if tests requested to use the DB (autouse)."""
    if tests_use_db and not request.config.getvalue('reuse_db'):
        return request.getfuncargvalue('post_db_setup')


def pytest_configure():
    if not settings.configured:
        from pootle import syspath_override  # Needed for monkey-patching
        syspath_override
        os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
        WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['POOTLE_SETTINGS'] = os.path.join(
            WORKING_DIR, 'settings.py')
        setup()  # Required until pytest-dev/pytest-django#146 is fixed


@pytest.fixture(autouse=True, scope="session")
def translations_directory(request):
    """used by PootleEnv"""
    from django.conf import settings

    settings.POOTLE_TRANSLATION_DIRECTORY = tempfile.mkdtemp()

    def rm_tmp_dir():
        shutil.rmtree(settings.POOTLE_TRANSLATION_DIRECTORY)

    request.addfinalizer(rm_tmp_dir)


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name


pytest_plugins = tuple(
    [p for p in _load_fixtures(fixtures, )])
