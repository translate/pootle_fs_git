# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.resources import FSProjectStateResources


class GitProjectStateResources(FSProjectStateResources):

    @property
    def file_hashes(self):
        _hashes = {}
        found = [x[1] for x in self.found_file_matches]
        for item in self.context.repo.tree().traverse():
            if "/%s" % item.path in found:
                _hashes["/%s" % item.path] = item.hexsha
        hashes = {}
        for pootle_path, path in self.found_file_matches:
            hashes[pootle_path] = _hashes[path]
        return hashes
