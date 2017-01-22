# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from pootle_fs.files import FSFile


logger = logging.getLogger(__name__)


class GitFSFile(FSFile):

    @property
    def repo(self):
        return self.plugin.repo

    @property
    def latest_hash(self):
        return self.repo.tree()[self.path[1:]].hexsha

    @property
    def latest_author(self):
        author = self.repo.commit().author
        return author.name, author.email
