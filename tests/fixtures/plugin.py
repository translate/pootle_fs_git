# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
import os

import pytest

from git import Repo

from pytest_pootle.fs.utils import create_test_suite

from pootle_fs_git.utils import tmp_git

DEFAULT_TRANSLATION_PATHS = OrderedDict(
    [("default", "gnu_style/po/<lang>.po"),
     ("subdir1",
      "gnu_style_named_folders/po-<filename>/<lang>.po"),
     ("subdir2",
      "gnu_style_named_files/po/<filename>-<lang>.po"),
     ("subdir3",
      "non_gnu_style/locales/<lang>/<directory_path>/<filename>.po")])


@contextmanager
def get_dir_util():
    from distutils import dir_util
    yield dir_util
    # bug in distutils cache
    dir_util._path_created = {}


@pytest.fixture(scope="session", autouse=True)
def git_env(post_db_setup, _django_cursor_wrapper):
    from django.conf import settings

    from pytest_pootle.utils import update_store
    from pytest_pootle.fs.utils import create_test_suite
    import pytest_pootle

    from pytest_pootle.factories import (
        ProjectDBFactory, TranslationProjectFactory)

    from pootle_app.models import Directory
    from pootle_config.utils import ObjectConfig
    from pootle_fs.projects import FSPlugin
    from pootle_language.models import Language
    from pootle_store.models import Store

    import tempfile

    with _django_cursor_wrapper:
        project0 = ProjectDBFactory(
            source_language=Language.objects.get(code="en"),
            code="git_project_0")

        language0 = Language.objects.get(code="language0")
        tp = TranslationProjectFactory(project=project0, language=language0)

        initial_src_path = os.path.abspath(
            os.path.join(
                os.path.dirname(pytest_pootle.__file__),
                "data/fs/example_fs"))
        fs_dir = tempfile.mkdtemp()
        settings.POOTLE_FS_PATH = fs_dir

        repo_path = os.path.join(fs_dir, "__git_src_project_0__")
        Repo.init(repo_path, bare=True)

        with tmp_git(repo_path) as (tmp_repo_path, tmp_repo):
            with get_dir_util() as dir_util:
                dir_util.copy_tree(initial_src_path, tmp_repo_path)
            tmp_repo.index.add([".pootle.ini", "*"])
            tmp_repo.index.commit("Initial commit")
            tmp_repo.remotes.origin.push("master:master")

        conf = ObjectConfig(project0)
        conf["pootle_fs.fs_type"] = "git"
        conf["pootle_fs.fs_url"] = repo_path
        conf["pootle_fs.translation_paths"] = OrderedDict(
            [("default", "gnu_style/po/<lang>.po"),
             ("subdir1",
              "gnu_style_named_folders/po-<filename>/<lang>.po"),
             ("subdir2",
              "gnu_style_named_files/po/<filename>-<lang>.po"),
             ("subdir3",
              "non_gnu_style/locales/<lang>/<directory_path>/<filename>.po")])

        updated_src_path = os.path.abspath(
            os.path.join(
                os.path.dirname(pytest_pootle.__file__),
                "data/fs/example_fs_updated"))

        plugin = FSPlugin(project0)
        plugin.add_translations()
        plugin.fetch_translations()
        plugin.sync_translations()

        with tmp_git(repo_path) as (tmp_repo_path, tmp_repo):
            # merge the update onto the repo src
            with get_dir_util() as dir_util:
                dir_util.copy_tree(
                    updated_src_path,
                    tmp_repo_path, preserve_times=0)
            tmp_repo.index.add([".pootle.ini", "*"])
            tmp_repo.index.commit("Creating test suite")
            tmp_repo.remotes.origin.push("master:master")

        # conflict
        pootle_path_conflict = (
            "%ssubdir3/subsubdir/example3.po"
            % tp.pootle_path)
        plugin.pull()
        update_store(
            Store.objects.get(pootle_path=pootle_path_conflict),
            units=(("Hello, world", "Hello, world DB CONFLICT"), ))

        # conflict_untracked
        subdir3 = Directory.objects.get(
            pootle_path="%ssubdir3/" % tp.pootle_path)
        Store.objects.create(
            translation_project=tp,
            parent=subdir3,
            name="example3.po")

        # pootle_ahead
        pootle_path_ahead = "%ssubdir1/example1.po" % tp.pootle_path
        update_store(
            Store.objects.get(pootle_path=pootle_path_ahead),
            units=(("Hello, world", "Hello, world DB AHEAD"), ))

        # pootle_untracked
        Store.objects.create(
            translation_project=tp,
            parent=subdir3,
            name="example4.po")

        # pootle_removed
        Store.objects.get(
            pootle_path="%ssubdir1/example2.po" % tp.pootle_path).delete()

        create_test_suite(plugin)

        project1 = ProjectDBFactory(
            source_language=Language.objects.get(code="en"),
            code="git_project_1")

        tp = TranslationProjectFactory(project=project1, language=language0)

        repo_path = os.path.join(fs_dir, "__git_src_project_1__")
        Repo.init(repo_path, bare=True)
        with tmp_git(repo_path) as (tmp_repo_path, tmp_repo):
            with get_dir_util() as dir_util:
                dir_util.copy_tree(initial_src_path, tmp_repo_path)
            tmp_repo.index.add(["*"])
            tmp_repo.index.commit("Initial commit")
            tmp_repo.remotes.origin.push("master:master")
        conf = ObjectConfig(project1)
        conf["pootle_fs.fs_type"] = "git"
        conf["pootle_fs.fs_url"] = repo_path
        conf["pootle_fs.translation_paths"] = OrderedDict(
            [("default", "gnu_style/po/<lang>.po"),
             ("subdir1",
              "gnu_style_named_folders/po-<filename>/<lang>.po"),
             ("subdir2",
              "gnu_style_named_files/po/<filename>-<lang>.po"),
             ("subdir3",
              "non_gnu_style/locales/<lang>/<directory_path>/<filename>.po")])


@pytest.fixture
def git_plugin_base(tmpdir, settings):
    from pootle_config.utils import ObjectConfig
    from pootle_fs.projects import FSPlugin
    from pootle_project.models import Project

    with get_dir_util() as dir_util:
        dir_util.copy_tree(
            settings.POOTLE_FS_PATH,
            str(tmpdir))
    settings.POOTLE_FS_PATH = str(tmpdir)
    for project_code in ["project_0", "project_1"]:
        project = Project.objects.get(
            code="git_%s" % project_code)
        repo_path = os.path.join(
            settings.POOTLE_FS_PATH,
            "__git_src_%s__" % project_code)
        conf = ObjectConfig(project)
        conf["pootle_fs.fs_type"] = "git"
        conf["pootle_fs.fs_url"] = repo_path
        conf["pootle_fs.translation_paths"] = DEFAULT_TRANSLATION_PATHS
        plugin = FSPlugin(project)
        if os.path.exists(plugin.local_fs_path):
            origin = plugin.repo.remotes.origin
            cw = origin.config_writer
            cw.set("url", plugin.fs_url)
            cw.release()


@pytest.fixture
def git_project(git_plugin_base):
    from pootle_project.models import Project

    return Project.objects.get(code="git_project_0")


@pytest.fixture
def git_project_1(git_plugin_base):
    from pootle_project.models import Project

    return Project.objects.get(code="git_project_1")


def _git_edit(plugin, filepath, content=None, message=None):
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        dir_name = os.path.dirname(po_file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if content is None:
            content = str(datetime.now())
        if message is None:
            message = "Editing %s" % filepath
        with open(po_file, "w") as f:
            f.write(content)
        tmp_repo.index.add([filepath.strip("/")])
        tmp_repo.index.commit(message)
        tmp_repo.remotes.origin.push()


def _git_remove(plugin, filepath):
    with tmp_git(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        os.unlink(po_file)
        tmp_repo.index.commit("Removing %s" % filepath)
        tmp_repo.remotes.origin.push()


@pytest.fixture
def git_plugin_suite(git_plugin):
    return create_test_suite(
        git_plugin, edit_file=_git_edit, remove_file=_git_remove)
