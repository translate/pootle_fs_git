#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest
from ConfigParser import ConfigParser

from pootle_fs.models import StoreFS
from pootle_fs_pytest.suite import (
    run_add_test, run_fetch_test, run_rm_test, run_merge_test)

from ..fixtures.plugin import tmp_git


def _check_git_fs(plugin, response):
    with tmp_git(plugin.repo) as (tmp_repo_path, tmp_repo):
        assert all(
            os.path.exists(
                os.path.join(
                    tmp_repo_path,
                    p.fs_path.strip("/")))
            for p
            in response["pushed_to_fs"])
        assert not any(
            os.path.exists(
                os.path.join(
                    tmp_repo_path,
                    p.fs_path.strip("/")))
            for p
            in response["pruned_from_fs"])

        for response in response["pushed_to_fs"]:
            store_fs = StoreFS.objects.get(pootle_path=response.pootle_path)
            serialized = store_fs.store.serialize()
            assert serialized == store_fs.file.read()
            # todo - also check that the version in git is the same


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
    run_fetch_test(
        git_plugin_suite,
        check_fs=_check_git_fs,
        **fetch_translations)


# Parametrized ADD
@pytest.mark.django
def test_plugin_add_translations(git_plugin_suite, add_translations):
    run_add_test(
        git_plugin_suite,
        check_fs=_check_git_fs,
        **add_translations)


# Parametrized RM
@pytest.mark.django
def test_plugin_rm_translations(git_plugin_suite, rm_translations):
    run_rm_test(
        git_plugin_suite,
        check_fs=_check_git_fs,
        **rm_translations)


# Parametrized MERGE
@pytest.mark.django
def test_plugin_merge_fs(git_plugin_suite, merge_translations):
    run_merge_test(
        git_plugin_suite,
        check_fs=_check_git_fs,
        **merge_translations)


# Parametrized MERGE
@pytest.mark.django
def test_plugin_merge_pootle(git_plugin_suite, merge_translations):
    run_merge_test(
        git_plugin_suite,
        check_fs=_check_git_fs,
        pootle_wins=True,
        **merge_translations)
