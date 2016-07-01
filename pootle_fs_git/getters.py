# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import response, state
from pootle.core.plugin import getter

from pootle_fs.delegate import fs_file, fs_finder, fs_matcher, fs_resources
from pootle_fs.finder import TranslationFileFinder
from pootle_fs.matcher import FSPathMatcher
from pootle_fs.resources import FSProjectResources
from pootle_fs.response import ProjectFSResponse
from pootle_fs.state import ProjectFSState

from .files import GitFSFile
from .plugin import GitPlugin


@getter(state, sender=GitPlugin)
def fs_plugin_state_getter(**kwargs):
    return ProjectFSState


@getter(response, sender=ProjectFSState)
def fs_plugin_response_getter(**kwargs):
    return ProjectFSResponse


@getter(fs_file, sender=GitPlugin)
def fs_file_getter(**kwargs):
    return GitFSFile


@getter(fs_resources, sender=GitPlugin)
def fs_resources_getter(**kwargs):
    return FSProjectResources


@getter(fs_finder, sender=GitPlugin)
def fs_finder_getter(**kwargs):
    return TranslationFileFinder


@getter(fs_matcher, sender=GitPlugin)
def fs_matcher_getter(**kwargs):
    return FSPathMatcher
