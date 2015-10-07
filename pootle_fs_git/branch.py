from contextlib import contextmanager
import logging
import uuid


logger = logging.getLogger(__name__)


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

    def commit(self, msg):
        # commit
        self.repo.index.add(["*"])
        self.repo.index.commit("Updating repo")
        logger.info(
            "Committing from git branch (%s): %s"
            % (self.project.code, self.name))

    def push(self):
        # push to remote/$master
        self.repo.remotes.origin.push(
            "%s:%s"
            % (self.name, self.master.name))
        # TODO: check the push summary info to ensure success
        logger.info(
            "Pushing to remote git branch (%s): %s"
            % (self.project.code, self.name))

    def destroy(self):
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
    yield branch
    branch.destroy()
