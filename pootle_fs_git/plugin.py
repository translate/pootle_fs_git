# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

from git import Actor, Repo

from pootle_fs.plugin import Plugin, responds_to_status

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MSG = "Translation files updated from Pootle"


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

    @property
    def author(self):
        author_name = self.config.get("pootle_fs.author_name")
        author_email = self.config.get("pootle_fs.author_email")
        if not (author_name and author_email):
            return None
        return Actor(
            self.config["pootle_fs.author_name"],
            self.config["pootle_fs.author_email"])

    @property
    def committer(self):
        committer_name = self.config.get("pootle_fs.committer_name")
        committer_email = self.config.get("pootle_fs.committer_email")
        if not (committer_name and committer_email):
            return None
        return Actor(
            self.config["pootle_fs.committer_name"],
            self.config["pootle_fs.committer_email"])

    @property
    def repo(self):
        return Repo(self.local_fs_path)

    def pull(self):
        super(GitPlugin, self).pull()
        if not self.is_cloned:
            logger.info(
                "Cloning git repository(%s): %s"
                % (self.project.code, self.fs_url))
            Repo.clone_from(self.fs_url, self.local_fs_path)
        else:
            logger.info(
                "Pulling git repository(%s): %s"
                % (self.project.code, self.fs_url))
        self.repo.remote().pull("master:master", force=True)

    def get_latest_hash(self):
        self.pull()
        return self.repo.commit().hexsha

    def get_commit_message(self, response):
        return self.config.get(
            "pootle_fs.commit_message",
            DEFAULT_COMMIT_MSG)

    @responds_to_status
    def push_translations(self, status, response, msg=None,
                          pootle_path=None, fs_path=None):
        try:
            with tmp_branch(self) as branch:
                response = self.push_translation_files(
                    pootle_path=pootle_path,
                    fs_path=fs_path, status=status,
                    response=response)
                if response.made_changes:
                    logger.info(
                        "Committing/pushing git repository(%s): %s"
                        % (self.project.code, self.fs_url))
                    add_paths = [
                        os.path.join(
                            self.local_fs_path,
                            x.fs_path.strip("/"))
                        for x
                        in response['pushed_to_fs']]
                    branch.add(add_paths)
                    # this is a bit of a dirty hack to
                    # prevent `git rm` on files that
                    # are not part of the repo
                    repo_paths = [
                        y.path for x, y
                        in self.repo.index.iter_blobs()]
                    branch.rm(
                        [os.path.join(self.local_fs_path,
                                      x.fs_path.strip("/"))
                         for x
                         in response['removed']
                         if x.fs_path.strip("/") in repo_paths])
                    branch.commit(
                        self.get_commit_message(response),
                        author=self.author,
                        committer=self.committer)
                    branch.push()
        except PushError as e:
            logger.exception(e)
            for action in response["pushed_to_fs"]:
                action.failed = True
            for action in response["removed"]:
                action.failed = True

        for action_status in response.completed("pushed_to_fs"):
            fs_file = action_status.store_fs.file
            fs_file.on_sync(
                fs_file.latest_hash,
                action_status.store_fs.store.get_max_unit_revision())
        return response
