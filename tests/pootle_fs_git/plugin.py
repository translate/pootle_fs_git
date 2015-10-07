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

from pootle_store.models import Store

from pootle_fs_pytest.utils import (
    _test_status)


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


@pytest.mark.django
def test_plugin_push_translations(git_plugin_pulled, expected_fs_stores):
    plugin = git_plugin_pulled

    # add a Store object
    sibling = plugin.stores.get(
        pootle_path="/en/tutorial/subdir1/example1.po")
    Store.objects.create(
        parent=sibling.parent,
        translation_project=sibling.translation_project,
        name="example5.po")

    status = plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_untracked"]) == 1

    plugin.add_translations()

    status = plugin.status()
    assert status.has_changed is True
    assert len(status["pootle_added"]) == 1

    plugin.push_translations()
    status = plugin.status()
    assert status.has_changed is False


# Parametrized PATH_FILTERS
@pytest.mark.django
def test_plugin_fetch_paths(git_fetch_paths):
    plugin, path, outcome = git_fetch_paths
    plugin.fetch_translations(**path)
    status = plugin.status()
    assert outcome == {k: len(status[k]) for k in status}


# Parametrized: CONFLICT
@pytest.mark.django
def test_plugin_conflict(git_plugin_conflicted_param):
    name, plugin, callback, outcome = git_plugin_conflicted_param
    conflict_type = "conflict"
    if name.startswith("conflict_untracked"):
        conflict_type = "conflict_untracked"
    conflict = plugin.status()[conflict_type]
    assert conflict
    callback(plugin)
    if not outcome:
        outcome = {
            conflict_type: [(x.pootle_path, x.fs_path) for x in conflict]}
    _test_status(plugin, outcome)
