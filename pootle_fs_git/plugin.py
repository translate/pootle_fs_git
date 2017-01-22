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
from git.exc import GitCommandError

from django.conf import settings

from pootle_fs.decorators import emits_state, responds_to_state
from pootle_fs.exceptions import FSFetchError
from pootle_fs.plugin import Plugin
from pootle_fs.signals import fs_pre_push, fs_post_push

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MSG = "Translation files updated from Pootle"


class Changelog(object):

    def __init__(self, response):
        self.response = response

    @property
    def commits(self):
        return self.by_author(self.response)

    def by_author(self, response):
        """Groups into a single commit, if there is more than one author
        credits, are added in commit message"""
        authors = set()
        paths = set()
        for resp in response.completed("pushed_to_fs", "merged_from_pootle"):
            if resp.store_fs.pootle_path in paths:
                continue
            paths.add(resp.store_fs.path)
            user = resp.store_fs.store.data.last_submission.submitter
            authors.add((user.username, user.email))
        return [dict(authors=authors, paths=paths)]


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

    @property
    def author(self):
        author_name = self.project.config.get(
            "pootle.fs.author_name",
            getattr(settings, "POOTLE_FS_AUTHOR", None))
        author_email = self.project.config.get(
            "pootle.fs.author_email",
            getattr(settings, "POOTLE_FS_AUTHOR_EMAIL", None))
        if not (author_name and author_email):
            return None
        return Actor(author_name, author_email)

    @property
    def committer(self):
        committer_name = self.project.config.get(
            "pootle.fs.committer_name",
            getattr(settings, "POOTLE_FS_COMMITTER", None))
        committer_email = self.project.config.get(
            "pootle.fs.committer_email",
            getattr(settings, "POOTLE_FS_COMMITTER_EMAIL", None))
        if not (committer_name and committer_email):
            return None
        return Actor(committer_name, committer_email)

    @property
    def repo(self):
        return Repo(self.project.local_fs_path)

    def fetch(self):
        if not self.is_cloned:
            logger.info(
                "Cloning git repository(%s): %s"
                % (self.project.code, self.fs_url))
            try:
                Repo.clone_from(self.fs_url, self.project.local_fs_path)
            except GitCommandError as e:
                raise FSFetchError(e)
        else:
            logger.info(
                "Pulling git repository(%s): %s"
                % (self.project.code, self.fs_url))
            try:
                self.repo.remote().pull("master:master", force=True)
            except GitCommandError as e:
                raise FSFetchError(e)

    @property
    def latest_hash(self):
        if self.is_cloned:
            return self.repo.commit().hexsha

    @property
    def commit_message(self):
        return self.project.config.get(
            "pootle.fs.commit_message",
            getattr(
                settings,
                "POOTLE_FS_AUTHOR",
                DEFAULT_COMMIT_MSG))

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

    def _commit_to_branch(self, branch, paths=(), authors=()):
        add_paths = [
            os.path.join(
                self.project.local_fs_path,
                path[1:])
            for path
            in paths]
        if len(authors) > 1:
            author = self.author
            commit_message = (
                "%s\n\nAuthors:\n%s"
                % (self.commit_message,
                   "\n".join(
                       [("%s (%s)" % (username, email))
                        for username, email in authors])))
        else:
            commit_message = self.commit_message
            author = Actor(*authors.pop())
        branch.add(add_paths)
        branch.commit(
            commit_message,
            author=author,
            committer=self.committer)

    def _push_to_branch(self, commits):
        try:
            with tmp_branch(self) as branch:
                for commit in commits:
                    self._commit_to_branch(branch, **commit)
                branch.push()
        except PushError as e:
            logger.exception(e)
            raise e

    def push(self, response):
        push_from_pootle = (
            "pushed_to_fs" in response
            or "merged_from_pootle" in response)
        if response.made_changes and push_from_pootle:
            try:
                self._push_to_branch(Changelog(response).commits)
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
