import logging

from pootle_fs import FSFile


logger = logging.getLogger(__name__)


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
