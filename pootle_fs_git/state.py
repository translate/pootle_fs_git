# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle_fs.state import ProjectFSState

from .resources import GitProjectStateResources


class GitProjectState(ProjectFSState):

    @cached_property
    def resources(self):
        return GitProjectStateResources(
            self.context,
            pootle_path=self.pootle_path,
            fs_path=self.fs_path)
