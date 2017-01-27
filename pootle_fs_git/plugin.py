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

from pootle_fs.exceptions import FSFetchError
from pootle_fs.plugin import Plugin

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MSG = "Translation files updated from Pootle"


class Commit(object):

    def __init__(self):
        self.to_add = set()
        self.to_remove = set()
        self.authors = set()

    def add(self, path):
        self.to_add.add(path)

    def remove(self, path):
        self.to_remove.add(path)

    def add_author(self, name, email):
        self.authors.add((name, email))

    @property
    def paths(self):
        return self.to_add.union(self.to_remove)


class Changelog(object):

    def __init__(self, plugin, response):
        self.plugin = plugin
        self.response = response

    @property
    def commits(self):
        return self.by_author(self.response)

    def by_author(self, response):
        """Groups into a single commit, if there is more than one author
        credits, are added in commit message"""
        commit = Commit()
        completed = response.completed(
            "pushed_to_fs", "merged_from_pootle", "removed", "merged_from_fs")
        tree = self.plugin.repo.tree()
        for resp in completed:
            if resp.pootle_path in commit.paths:
                continue
            if resp.action_type == "removed":
                try:
                    tree[resp.fs_path[1:]]
                    commit.remove(resp.fs_path)
                except KeyError:
                    pass
            else:
                commit.add(resp.fs_path)
                user = resp.store_fs.store.data.last_submission.submitter
                commit.add_author(user.display_name, user.email)
        return [commit]


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

    def _commit_to_branch(self, branch, commit):
        add_paths = [
            os.path.join(
                self.project.local_fs_path,
                path[1:])
            for path
            in commit.to_add]
        if len(commit.authors) > 1:
            author = self.author
            commit_message = (
                "%s\n\nAuthors:\n%s"
                % (self.commit_message,
                   "\n".join(
                       [("%s <%s>" % (display_name, email))
                        for display_name, email in commit.authors])))
        else:
            commit_message = self.commit_message
            author = (
                Actor(*commit.authors.pop())
                if commit.authors
                else self.author)
        branch.rm(commit.to_remove)
        branch.add(add_paths)
        if self.repo.is_dirty():
            branch.commit(
                commit_message,
                author=author,
                committer=self.committer)
            return True

    def _push_to_branch(self, changelog):
        pushed = False
        try:
            with tmp_branch(self) as branch:
                for commit in changelog.commits:
                    if commit.paths:
                        _pushed = self._commit_to_branch(branch, commit)
                        pushed = pushed or _pushed
                if pushed:
                    branch.push()
        except PushError as e:
            logger.exception(e)
            raise e

    def push(self, response):
        push_from_pootle = (
            "pushed_to_fs" in response
            or "merged_from_pootle" in response
            or "merged_from_fs" in response
            or "removed" in response)
        if response.made_changes and push_from_pootle:
            try:
                self._push_to_branch(Changelog(self, response))
            except PushError as e:
                for action in response["pushed_to_fs"]:
                    action.failed = True
                for action in response["merged_from_pootle"]:
                    action.failed = True
                for action in response["merged_from_fs"]:
                    action.failed = True
                for action in response["removed"]:
                    action.failed = True
                raise e
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
