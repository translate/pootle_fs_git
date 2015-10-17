import logging
import os

from git import Repo

from pootle_fs import Plugin

from .branch import tmp_branch, PushError
from .files import GitFSFile


logger = logging.getLogger(__name__)


class GitPlugin(Plugin):
    name = "git"
    file_class = GitFSFile

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

    def push_translations(self, msg=None, pootle_path=None, fs_path=None,
                          response=None, status=None):
        if status is None:
            status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        if response is None:
            response or self.response_class(self)
        if not status.has_changed:
            return
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
                        in response['pushed_to_fs']]
                    branch.add(add_paths)
                    # this is a bit of a dirty hack to
                    # prevent `git rm` on files that
                    # are not part of the repo
                    repo_paths = [
                        x for x
                        in self.repo.index.iter_blobs()]
                    rm_paths = [
                        os.path.join(
                            self.local_fs_path,
                            x.fs_path.strip("/"))
                        for x
                        in response['removed']
                        if x.fs_path.strip("/") in repo_paths]
                    branch.rm(rm_paths)
                    branch.commit(msg)
                    branch.push()
        except PushError:
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
