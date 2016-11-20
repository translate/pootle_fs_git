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

from pootle_fs.decorators import emits_state, responds_to_state
from pootle_fs.plugin import Plugin
from pootle_fs.signals import fs_pre_push, fs_post_push

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MSG = "Translation files updated from Pootle"


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

    @property
    def author(self):
        # author_name = self.config.get("pootle_fs.author_name")
        # author_email = self.config.get("pootle_fs.author_email")
        # if not (author_name and author_email):
        #    return None
        return Actor("phlax", "ryan@synca.io")
        #    self.config["pootle_fs.author_name"],
        #    self.config["pootle_fs.author_email"])

    @property
    def committer(self):
        #        committer_name = self.config.get("pootle_fs.committer_name")
        #        committer_email = self.config.get("pootle_fs.committer_email")
        #       if not (committer_name and committer_email):
        #           return None
        return Actor("phlax", "ryan@synca.io")
    #        return Actor(
    #            self.config["pootle_fs.committer_name"],
    #            self.config["pootle_fs.committer_email"])

    @property
    def repo(self):
        return Repo(self.project.local_fs_path)

    def fetch(self):
        if not self.is_cloned:
            logger.info(
                "Cloning git repository(%s): %s"
                % (self.project.code, self.fs_url))
            Repo.clone_from(self.fs_url, self.project.local_fs_path)
        else:
            logger.info(
                "Pulling git repository(%s): %s"
                % (self.project.code, self.fs_url))
        self.repo.remote().pull("master:master", force=True)

    @property
    def latest_hash(self):
        if self.is_cloned:
            return self.repo.commit().hexsha

    def get_commit_message(self, response):
        return DEFAULT_COMMIT_MSG
        # return self.config.get(
        #    "pootle_fs.commit_message",
        #    DEFAULT_COMMIT_MSG)

    @responds_to_state
    @emits_state(pre=fs_pre_push, post=fs_post_push)
    def sync_push(self, state, response, fs_path=None, pootle_path=None):
        """
        Push translations from Pootle to working directory.

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of
          self.respose_class
        """
        pushable = (
            state['pootle_staged']
            + state['pootle_ahead']
            + state["merge_fs_wins"])
        for fs_state in pushable:
            fs_state.store_fs.file.push()
            response.add('pushed_to_fs', fs_state=fs_state)
        return response

    def _commit_to_branch(self, branch, path, authors):
        add_paths = [
            os.path.join(
                self.project.local_fs_path,
                path[1:])
            for x
            in [path]]
        author = authors.pop()
        branch.add(add_paths)
        # self.get_commit_message(response)
        branch.commit(
            "Updating from Pootle",
            author=author,
            committer=self.committer)

    def _push_to_branch(self, commits):
        try:
            with tmp_branch(self) as branch:
                # logger.info(
                #    "Committing/pushing git repository(%s): %s"
                #    % (self.project.code, self.fs_url))
                for commit in commits:
                    self._commit_to_branch(branch, *commit)
                branch.push()
        except PushError as e:
            logger.exception(e)
            raise e

    def _map_authors_to_commits(self, response):
        stores = {}
        _commits = {}
        for resp in response.completed("pushed_to_fs", "merged_from_pootle"):
            store = resp.store_fs.store
            last_sync = resp.store_fs.last_sync_revision
            if last_sync:
                units_between = store.unit_set.filter(revision__gt=last_sync)
            else:
                units_between = store.unit_set.all()
            stores[resp.store_fs.path] = []
            changed_units = units_between.values_list(
                "revision",
                "submitted_by__username",
                "submitted_by__full_name",
                "submitted_by__email")
            for revision, username, fullname, email in changed_units:
                author = Actor(fullname or username, email)
                stores[resp.store_fs.path].append((revision, author))
        for store, data in stores.items():
            commit_revision = max([x[0] for x in data])
            authors = set([x[1] for x in data])
            _commits[commit_revision] = _commits.get(commit_revision, [])
            _commits[commit_revision].append((store, authors))
        commits = []
        for revision in sorted(_commits.keys()):
            commit = _commits[revision]
            for store, authors in commit:
                commits.append((store, authors))
        return commits

    def push(self, response):
        push_from_pootle = (
            "pushed_to_fs" in response
            or "merged_from_pootle" in response)
        if response.made_changes and push_from_pootle:
            commits = self._map_authors_to_commits(response)
            try:
                self._push_to_branch(commits)
            except PushError as e:
                raise e
                for action in response["pushed_to_fs"]:
                    action.failed = True
                for action in response["merged_from_pootle"]:
                    action.failed = True
                for action in response["removed"]:
                    action.failed = True
        return response

    def get_file_hash(self, path):
        file_path = os.path.join(
            self.project.local_fs_path,
            path.strip("/"))
        if os.path.exists(file_path):
            return self.repo.git.log(
                '-1',
                '--pretty=%H',
                '--follow',
                '--',
                file_path)
