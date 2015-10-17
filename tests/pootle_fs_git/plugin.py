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

from pootle_fs_git.plugin import DEFAULT_COMMIT_MSG

from ..fixtures.plugin import tmp_git


def _check_git_fs(plugin, response):
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
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


@pytest.mark.django
def test_plugin_commit_message(git_plugin_suite):
    NEW_COMMIT_MSG = "New commit message"
    plugin = git_plugin_suite
    plugin.pull()
    config = plugin.read_config()
    assert not config.has_option("default", "commit_message")

    # make some updates
    plugin.push_translations()

    # check that commit message uses default when not set in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.git.log('-1', '--pretty=%s')
        assert last_commit == DEFAULT_COMMIT_MSG

    # update the commit message in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        config.set("default", "commit_message", NEW_COMMIT_MSG)
        config.write(
            open(
                os.path.join(tmp_repo_path, ".pootle.ini"), "w"))
        tmp_repo.index.add([".pootle.ini"])
        tmp_repo.index.commit("Updating .pootle.ini")
        tmp_repo.remotes.origin.push()

    # update config
    plugin.update_config()

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit message
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.git.log('-1', '--pretty=%s')
        assert last_commit == NEW_COMMIT_MSG


@pytest.mark.django
def test_plugin_commit_author(git_plugin_suite):
    NEW_AUTHOR_NAME = "New Author"
    NEW_AUTHOR_EMAIL = "new@email.address"
    plugin = git_plugin_suite
    plugin.pull()
    config = plugin.read_config()
    assert not config.has_option("default", "author_name")
    assert not config.has_option("default", "author_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.git.log('-1', '--pretty=%ae')
        git_config = tmp_repo.config_reader()
        assert last_author_name == git_config.get_value("user", "name")
        assert last_author_email == git_config.get_value("user", "email")

    # update the author name/email in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        config.set("default", "author_name", NEW_AUTHOR_NAME)
        config.set("default", "author_email", NEW_AUTHOR_EMAIL)
        config.write(
            open(
                os.path.join(tmp_repo_path, ".pootle.ini"), "w"))
        tmp_repo.index.add([".pootle.ini"])
        tmp_repo.index.commit("Updating .pootle.ini")
        tmp_repo.remotes.origin.push()

    # update config
    plugin.update_config()

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit author
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.git.log('-1', '--pretty=%ae')
        assert last_author_name == NEW_AUTHOR_NAME
        assert last_author_email == NEW_AUTHOR_EMAIL


@pytest.mark.django
def test_plugin_commit_committer(git_plugin_suite):
    NEW_COMMITTER_NAME = "New Committer"
    NEW_COMMITTER_EMAIL = "new@email.address"
    plugin = git_plugin_suite
    plugin.pull()
    config = plugin.read_config()
    assert not config.has_option("default", "committer_name")
    assert not config.has_option("default", "committer_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_committer_email = tmp_repo.git.log('-1', '--pretty=%ae')
        git_config = tmp_repo.config_reader()
        assert last_committer_name == git_config.get_value("user", "name")
        assert last_committer_email == git_config.get_value("user", "email")

    # update the committer name/email in config
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        config.set("default", "committer_name", NEW_COMMITTER_NAME)
        config.set("default", "committer_email", NEW_COMMITTER_EMAIL)
        config.write(
            open(
                os.path.join(tmp_repo_path, ".pootle.ini"), "w"))
        tmp_repo.index.add([".pootle.ini"])
        tmp_repo.index.commit("Updating .pootle.ini")
        tmp_repo.remotes.origin.push()

    # update config
    plugin.update_config()

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit committer
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.git.log('-1', '--pretty=%cn')
        last_committer_email = tmp_repo.git.log('-1', '--pretty=%ce')
        assert last_committer_name == NEW_COMMITTER_NAME
        assert last_committer_email == NEW_COMMITTER_EMAIL


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
