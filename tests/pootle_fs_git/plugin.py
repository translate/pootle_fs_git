#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest
from ConfigParser import ConfigParser

from pootle_fs_pytest.suite import (
    run_add_test, run_fetch_test, run_pull_test, run_push_test)


@pytest.mark.django
def test_plugin_instance(git_plugin):
    assert git_plugin.project == git_plugin.fs.project
    assert git_plugin.local_fs_path.endswith(git_plugin.project.code)
    assert git_plugin.is_cloned is False
    assert git_plugin.stores.exists() is False
    assert git_plugin.translations.exists() is False


@pytest.mark.django
def test_plugin_instance_bad_args(git_plugin):

    with pytest.raises(TypeError):
        git_plugin.__class__()

    with pytest.raises(TypeError):
        git_plugin.__class__("FOO")


@pytest.mark.django
def test_plugin_pull(git_plugin):
    assert git_plugin.is_cloned is False
    git_plugin.pull()
    assert git_plugin.is_cloned is True


@pytest.mark.django
def test_plugin_read_config(git_plugin):
    git_plugin.pull()
    config = git_plugin.read_config()
    assert isinstance(config, ConfigParser)
    assert config.sections() == ['default', 'subdir1', 'subdir2', 'subdir3']


# Parametrized FETCH
@pytest.mark.django
def test_plugin_fetch_translations(git_plugin_suite, fetch_translations):
    run_fetch_test(git_plugin_suite, **fetch_translations)


# Parametrized ADD
@pytest.mark.django
def test_plugin_add_translations(git_plugin_suite, add_translations):
    run_add_test(git_plugin_suite, **add_translations)


# Parametrized PUSH
@pytest.mark.django
def test_plugin_push_translations(git_plugin_suite, push_translations):
    run_push_test(git_plugin_suite, **push_translations)


# Parametrized PULL
@pytest.mark.django
def test_plugin_pull_translations(git_plugin_suite, pull_translations):
    run_pull_test(git_plugin_suite, **pull_translations)
