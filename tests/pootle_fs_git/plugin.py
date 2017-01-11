# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import shutil
import os

import pytest

from pytest_pootle.factories import ProjectDBFactory
# from pytest_pootle.fs.suite import (
#    run_add_test, run_fetch_test, run_rm_test, run_merge_test,
#    check_files_match)

from pootle_fs.utils import FSPlugin

from pootle_config.utils import ObjectConfig

from pootle_fs_git.plugin import DEFAULT_COMMIT_MSG
from pootle_fs_git.utils import tmp_git

from ..fixtures.plugin import DEFAULT_TRANSLATION_PATHS


def _check_git_fs(plugin, response):
    # with tmp_git(plugin.fs_url) as (tmp_repo_path, tmp_repo):
    #   check_files_match(tmp_repo_path, response)
    pass


@pytest.mark.django_db
def test_plugin_instance(english):
    project = ProjectDBFactory(source_language=english)
    project.config["pootle_fs.fs_type"] = "git"
    project.config["pootle_fs.fs_url"] = "bar"
    project.config["pootle_fs.translation_paths"] = DEFAULT_TRANSLATION_PATHS
    git_plugin = FSPlugin(project)
    assert git_plugin.project == git_plugin.plugin.project == project
    assert git_plugin.is_cloned is False
    # assert git_plugin.stores.exists() is False
    # assert git_plugin.translations.exists() is False


@pytest.mark.django_db
def test_plugin_instance_bad_args(git_project):
    git_plugin = FSPlugin(git_project)

    with pytest.raises(TypeError):
        git_plugin.plugin.__class__()

    with pytest.raises(TypeError):
        git_plugin.plugin.__class__("FOO")


@pytest.mark.django_db
def test_plugin_fetch(git_project_1):
    git_plugin = FSPlugin(git_project_1)
    shutil.rmtree(git_plugin.project.local_fs_path)
    assert git_plugin.is_cloned is False
    git_plugin.fetch()
    assert git_plugin.is_cloned is True


@pytest.mark.django_db
def __test_plugin_commit_message(git_project):
    git_plugin = FSPlugin(git_project)
    NEW_COMMIT_MSG = "New commit message"
    git_plugin.pull()
    assert not git_plugin.config.get("pootle_fs.commit_message")

    # make some updates
    git_plugin.push_translations()

    # check that commit message uses default when not set in config
    with tmp_git(git_plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.git.log('-1', '--pretty=%s')
        assert last_commit == DEFAULT_COMMIT_MSG

    # update the config
    git_plugin.config["pootle_fs.commit_message"] = NEW_COMMIT_MSG

    # make further updates
    git_plugin.add_translations()
    git_plugin.sync_translations()

    # test that sync_translations committed with new commit message
    with tmp_git(git_plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.git.log('-1', '--pretty=%s')
        assert last_commit == NEW_COMMIT_MSG


@pytest.mark.django_db
def __test_plugin_commit_author(git_project):
    plugin = FSPlugin(git_project)

    NEW_AUTHOR_NAME = "New Author"
    NEW_AUTHOR_EMAIL = "new@email.address"
    plugin.pull()
    assert not plugin.config.get("pootle_fs.author_name")
    assert not plugin.config.get("pootle_fs.author_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_git(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.git.log('-1', '--pretty=%ae')
        git_config = tmp_repo.config_reader()
        default_user = os.environ["USER"]
        default_email = (
            "%s@%s"
            % (default_user, os.environ.get("HOSTNAME", "")))
        assert (
            last_author_name
            == git_config.get_value("user", "name", default_user))
        assert (
            last_author_email
            == git_config.get_value("user", "email", default_email))

    # update the author name/email in config
    plugin.config["pootle_fs.author_name"] = NEW_AUTHOR_NAME
    plugin.config["pootle_fs.author_email"] = NEW_AUTHOR_EMAIL

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit author
    with tmp_git(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.git.log('-1', '--pretty=%ae')
        assert last_author_name == NEW_AUTHOR_NAME
        assert last_author_email == NEW_AUTHOR_EMAIL


@pytest.mark.django_db
def __test_plugin_commit_committer(git_project):
    plugin = FSPlugin(git_project)

    NEW_COMMITTER_NAME = "New Committer"
    NEW_COMMITTER_EMAIL = "new@email.address"

    plugin.pull()
    assert not plugin.config.get("pootle_fs.committer_name")
    assert not plugin.config.get("pootle_fs.committer_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_git(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.git.log('-1', '--pretty=%an')
        last_committer_email = tmp_repo.git.log('-1', '--pretty=%ae')
        git_config = tmp_repo.config_reader()
        default_user = os.environ["USER"]
        default_email = (
            "%s@%s"
            % (default_user, os.environ.get("HOSTNAME", "")))
        assert (
            last_committer_name
            == git_config.get_value("user", "name", default_user))
        assert (
            last_committer_email
            == git_config.get_value("user", "email", default_email))

    # update the committer name/email in config
    plugin.config["pootle_fs.committer_name"] = NEW_COMMITTER_NAME
    plugin.config["pootle_fs.committer_email"] = NEW_COMMITTER_EMAIL

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit committer
    with tmp_git(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.git.log('-1', '--pretty=%cn')
        last_committer_email = tmp_repo.git.log('-1', '--pretty=%ce')
        assert last_committer_name == NEW_COMMITTER_NAME
        assert last_committer_email == NEW_COMMITTER_EMAIL


# Parametrized FETCH
@pytest.mark.django_db
def __test_plugin_fetch_translations(git_project, fetch_translations):
    # run_fetch_test(
    #    plugin=FSPlugin(git_project),
    #    check_fs=_check_git_fs,
    #    **fetch_translations)
    pass


# Parametrized ADD
@pytest.mark.django_db
def __test_plugin_add_translations(git_project, add_translations):
    # run_add_test(
    #    plugin=FSPlugin(git_project),
    #    check_fs=_check_git_fs,
    #    **add_translations)
    pass


# Parametrized RM
@pytest.mark.django_db
def __test_plugin_rm_translations(git_project, rm_translations):
    # run_rm_test(
    #    plugin=FSPlugin(git_project),
    #    check_fs=_check_git_fs,
    #    **rm_translations)
    pass


# Parametrized MERGE
@pytest.mark.django_db
def __test_plugin_merge_fs(git_project, merge_translations):
    # run_merge_test(
    #    plugin=FSPlugin(git_project),
    #    check_fs=_check_git_fs,
    #    **merge_translations)
    pass


# Parametrized MERGE
@pytest.mark.django_db
def __test_plugin_merge_pootle(git_project, merge_translations):
    # run_merge_test(
    #    plugin=FSPlugin(git_project),
    #    check_fs=_check_git_fs,
    #    pootle_wins=True,
    #    **merge_translations)
    pass
