from git import Repo

from pootle_fs import Plugin, plugins, FSFile


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
            Repo.clone_from(self.fs.url, self.local_fs_path)
        self.repo.remote().pull()

    def get_latest_hash(self):
        self.pull()
        return self.repo.commit().hexsha

plugins.register(GitPlugin)
