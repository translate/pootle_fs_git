
import os
import shutil

import pytest

from git import Repo

from pootle_fs_pytest.plugin import (
    PLUGIN_FETCH_PATHS, CONFLICT)
from pootle_fs_pytest.utils import (
    _register_plugin,
    _clear_fs, _edit_file, _setup_dir, _setup_store,
    _update_store)


@pytest.fixture
def git_plugin(tutorial, tmpdir, settings, system, english, zulu):
    from pootle_fs.models import ProjectFS

    import pootle_fs_pytest

    dir_path = str(tmpdir.dirpath())

    src_path = os.path.abspath(
        os.path.join(
            os.path.dirname(pootle_fs_pytest.__file__),
            "data/fs/example_fs"))
    repo_path = os.path.join(dir_path, "__git_src__")
    tmp_repo_path = os.path.join(dir_path, "__tmp_git_src__")
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    if os.path.exists(tmp_repo_path):
        shutil.rmtree(tmp_repo_path)
    repo = Repo.init(repo_path, bare=True)
    tmp_repo = repo.clone(tmp_repo_path)
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
    settings.POOTLE_FS_PATH = dir_path
    tutorial_path = os.path.join(dir_path, tutorial.code)
    if os.path.exists(tutorial_path):
        shutil.rmtree(tutorial_path)
    return ProjectFS.objects.create(
        project=tutorial,
        fs_type="git",
        url=repo_path).plugin


@pytest.fixture
def git_plugin_fetched(git_plugin):
    git_plugin.fetch_translations()
    return git_plugin


@pytest.fixture
def git_plugin_pulled(git_plugin_fetched):
    git_plugin_fetched.pull_translations()
    return git_plugin_fetched


@pytest.fixture
def git_fetch_paths(git_plugin_pulled, plugin_fetch_paths):
    _edit_file(git_plugin_pulled, "non_gnu_style/locales/en/foo/bar/baz.po")
    return [git_plugin_pulled] + list(PLUGIN_FETCH_PATHS[plugin_fetch_paths])


@pytest.fixture
def git_plugin_conflicted_param(conflict_outcomes, tutorial_fs,
                                tmpdir, settings, system):
    dir_path = str(tmpdir.dirpath())
    settings.POOTLE_FS_PATH = dir_path
    _clear_fs(dir_path, tutorial_fs)
    if conflict_outcomes.startswith("conflict_untracked"):
        plugin = _register_plugin(src=_setup_dir(dir_path))
    else:
        plugin = _register_plugin()

    plugin = plugin(tutorial_fs)
    if conflict_outcomes.startswith("conflict_untracked"):
        _setup_store(tutorial_fs)
    else:
        plugin.fetch_translations()
        plugin.pull_translations()
        _edit_file(plugin, "gnu_style/po/en.po")
        _update_store(plugin)

    return ([conflict_outcomes, plugin]
            + list(CONFLICT[conflict_outcomes]))
