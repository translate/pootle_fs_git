from contextlib import contextmanager
import logging
import uuid

from git import Repo

from pootle_fs import Plugin, plugins, FSFile


logger = logging.getLogger(__name__)


class GitBranch(object):

    def __init__(self, plugin, name):
        self.plugin = plugin
        self.name = name
        # get current branch as $master

    @property
    def project(self):
        return self.plugin.project

    @property
    def exists(self):
        return

    @property
    def is_active(self):
        return

    def create(self):
        logger.info(
            "Creating git branch (%s): %s"
            % (self.project.code, self.name))

    def checkout(self):
        if not self.exists:
            self.create()
        if not self.is_active:
            logger.info(
                "Checking out git branch (%s): %s"
                % (self.project.code, self.name))

    def commit(self, msg):
        # commit
        logger.info(
            "Committing from git branch (%s): %s"
            % (self.project.code, self.name))

    def push(self):
        # push to remote/$master
        logger.info(
            "Pushing to remote git branch (%s): %s"
            % (self.project.code, self.name))

    def destroy(self):
        logger.info(
            "Destroying git branch (%s): %s"
            % (self.project.code, self.name))
        # checkout $master
        # remove the branch
        pass


@contextmanager
def tmp_branch(plugin):
    branch = GitBranch(plugin, uuid.uuid4().hex)
    branch.checkout()
    yield branch
    branch.destroy()


class GitFSFile(FSFile):

    @property
    def repo(self):
        return self.fs.plugin.repo

    @property
    def latest_hash(self):
        return self.repo.git.log(
            '-1',
            '--pretty=%H',
            '--follow',
            '--',
            self.file_path)


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

    @property
    def repo(self):
        return Repo(self.local_fs_path)

    def pull(self):
        if not self.is_cloned:
            logger.info(
                "Cloning git repository(%s): %s"
                % (self.project.code, self.fs.url))
            Repo.clone_from(self.fs.url, self.local_fs_path)
        else:
            logger.info(
                "Pulling git repository(%s): %s"
                % (self.project.code, self.fs.url))
        self.repo.remote().pull()

    def get_latest_hash(self):
        self.pull()
        return self.repo.commit().hexsha

    def create_branch(self):
        # create a git branch
        # check it out
        pass

    def push_branch(self, branch):
        # push to origin
        # if merge conflict:
        #    try: rebase to origin
        #    try: push to origin
        #    except: give up
        pass

    def destroy_branch(self, branch):
        # checkout master
        pass

    def push_translations(self, msg=None, prune=False,
                          pootle_path=None, fs_path=None):
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        with tmp_branch(self) as branch:
            logger.info(
                "Committing/pushing git repository(%s): %s"
                % (self.project.code, self.fs.url))
            super(GitPlugin, self).push_translations(
                prune=prune, pootle_path=pootle_path,
                fs_path=fs_path, status=status)
            branch.commit(msg)
            branch.push()

plugins.register(GitPlugin)
