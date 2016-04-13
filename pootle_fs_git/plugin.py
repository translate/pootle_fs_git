from ConfigParser import NoOptionError
import logging
import os

from git import Actor, Repo

from pootle_fs import Plugin
from pootle_fs.plugin import responds_to_status

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)

DEFAULT_COMMIT_MSG = "Translation files updated from Pootle"


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

    @property
    def author(self):
        config = self.read_config()
        try:
            return Actor(
                config.get("default", "author_name"),
                config.get("default", "author_email"))
        except NoOptionError:
            return None

    @property
    def committer(self):
        config = self.read_config()
        try:
            return Actor(
                config.get("default", "committer_name"),
                config.get("default", "committer_email"))
        except NoOptionError:
            return None

    @property
    def repo(self):
        return Repo(self.local_fs_path)

    def pull(self):
        super(GitPlugin, self).pull()
        if not self.is_cloned:
            logger.info(
                "Cloning git repository(%s): %s"
                % (self.project.code, self.fs.url))
            Repo.clone_from(self.fs.url, self.local_fs_path)
        else:
            logger.info(
                "Pulling git repository(%s): %s"
                % (self.project.code, self.fs.url))
        self.repo.remote().pull("master:master", force=True)

    def get_latest_hash(self):
        self.pull()
        return self.repo.commit().hexsha

    def get_commit_message(self, response):
        config = self.read_config()
        if config.has_option("default", "commit_message"):
            return config.get("default", "commit_message")
        return DEFAULT_COMMIT_MSG

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
                        % (self.project.code, self.fs.url))
                    add_paths = [
                        os.path.join(
                            self.local_fs_path,
                            x.fs_path.strip("/"))
                        for x
                        in (response['pushed_to_fs']
                            + response['merged_from_pootle'])]
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
            for action in response["merged_from_pootle"]:
                action.failed = True
            for action in response["removed"]:
                action.failed = True
        fs_updated = (
            list(response.completed("pushed_to_fs"))
            + list(response.completed("merged_from_pootle")))
        for action_status in fs_updated:
            fs_file = action_status.store_fs.file
            fs_file.on_sync(
                fs_file.latest_hash,
                action_status.store_fs.store.get_max_unit_revision())
        return response
