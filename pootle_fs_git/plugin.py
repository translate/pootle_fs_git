import logging

from git import Repo

from pootle_fs import Plugin

from .branch import tmp_branch
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

    def push_translations(self, msg=None, prune=False,
                          pootle_path=None, fs_path=None):
        status = self.status(pootle_path=pootle_path, fs_path=fs_path)
        with tmp_branch(self) as branch:
            pushed, pruned = self.push_translation_files(
                prune=prune, pootle_path=pootle_path,
                fs_path=fs_path, status=status)
            if pushed or pruned:
                logger.info(
                    "Committing/pushing git repository(%s): %s"
                    % (self.project.code, self.fs.url))
                branch.commit(msg)
                branch.push()
        for status in pushed:
            fs_file = status.store_fs.file
            fs_file.on_sync(
                fs_file.latest_hash,
                status.store_fs.store.get_max_unit_revision())
