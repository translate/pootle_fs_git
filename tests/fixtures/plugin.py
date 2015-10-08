from contextlib import contextmanager
from datetime import datetime
import os
import shutil

import pytest

from git import Repo

from pootle_fs_pytest.utils import (
    create_test_suite, create_plugin)


@contextmanager
def tmp_git(repo):
    from django.conf import settings
    tmp_repo_path = os.path.join(
        settings.POOTLE_FS_PATH, "__tmp_git_src__")
    if os.path.exists(tmp_repo_path):
        shutil.rmtree(tmp_repo_path)
    tmp_repo = repo.clone(tmp_repo_path)
    yield tmp_repo_path, tmp_repo
    shutil.rmtree(tmp_repo_path)


@pytest.fixture
def git_plugin(fs_plugin_base):
    tutorial, src_path, repo_path, dir_path = fs_plugin_base
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    repo = Repo.init(repo_path, bare=True)
    with tmp_git(repo) as (tmp_repo_path, tmp_repo):
        for f in os.listdir(src_path):
            src = os.path.join(src_path, f)
            target = os.path.join(tmp_repo_path, f)
            if os.path.isdir(src):
                shutil.copytree(src, target)
            else:
                shutil.copyfile(src, target)
        tmp_repo.index.add([".pootle.ini", "*"])
        tmp_repo.index.commit("Initial commit")
        tmp_repo.remotes.origin.push()
    return create_plugin("git", fs_plugin_base)


def _git_edit(plugin, filepath):
    with tmp_git(plugin.repo) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        dir_name = os.path.dirname(po_file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(po_file, "w") as f:
            f.write(str(datetime.now()))
        tmp_repo.index.add([filepath.strip("/")])
        tmp_repo.index.commit("Editing %s" % filepath)
        tmp_repo.remotes.origin.push()


def _git_remove(plugin, filepath):
    with tmp_git(plugin.repo) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        os.unlink(po_file)
        tmp_repo.index.commit("Removing %s" % filepath)
        tmp_repo.remotes.origin.push()


@pytest.fixture
def git_plugin_suite(git_plugin):
    return create_test_suite(
        git_plugin, edit_file=_git_edit, remove_file=_git_remove)
