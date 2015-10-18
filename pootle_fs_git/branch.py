from contextlib import contextmanager
import logging
import uuid


logger = logging.getLogger(__name__)


class PushError(Exception):
    pass


class GitBranch(object):

    def __init__(self, plugin, name):
        self.plugin = plugin
        self.name = name
        self.master = self.repo.active_branch

    @property
    def exists(self):
        return self.name in [h.name for h in self.repo.heads]

    @property
    def project(self):
        return self.plugin.project

    @property
    def repo(self):
        return self.plugin.repo

    @property
    def is_active(self):
        return self.repo.active_branch.name == self.name

    @property
    def branch(self):
        if not self.exists:
            self.__branch__ = self.create()
        return self.__branch__

    def create(self):
        logger.info(
            "Creating git branch (%s): %s"
            % (self.project.code, self.name))
        origin = self.master.tracking_branch()
        branch = self.repo.create_head(self.name, origin)
        branch.set_tracking_branch(origin)
        return branch

    def checkout(self):
        if not self.is_active:
            self.branch.checkout()
            logger.info(
                "Checking out git branch (%s): %s"
                % (self.project.code, self.name))

    def add(self, paths):
        if paths:
            self.repo.index.add(paths)
            logger.info(
                "Adding paths (%s): %s"
                % (self.project.code, self.name))

    def rm(self, paths):
        if paths:
            self.repo.index.remove(paths)
            logger.info(
                "Removing path (%s): %s"
                % (self.project.code, self.name))

    def commit(self, msg, author=None, committer=None):
        # commit
        self.repo.index.commit(
            msg, author=author, committer=committer)
        logger.info(
            "Committing from git branch (%s): %s"
            % (self.project.code, self.name))

    def push(self):
        # push to remote/$master
        result = self.repo.remotes.origin.push(
            "%s:%s"
            % (self.name, self.master.name))

        if result[0].flags != 256:
            raise PushError("Commit was unsuccessful")

        logger.info(
            "Pushing to remote git branch (%s): %s"
            % (self.project.code, self.name))

    def destroy(self):
        self.repo.git.reset("--hard", "HEAD")
        self.master.checkout()
        self.repo.delete_head(self.name)
        self.repo.remotes.origin.pull()
        logger.info(
            "Destroying git branch (%s): %s"
            % (self.project.code, self.name))


@contextmanager
def tmp_branch(plugin):
    branch = GitBranch(plugin, uuid.uuid4().hex)
    branch.checkout()
    try:
        yield branch
    finally:
        branch.destroy()
