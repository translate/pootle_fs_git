# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import state
from pootle.core.plugin import getter, provider
from pootle_fs.delegate import fs_plugins
from pootle_fs.finder import TranslationFileFinder
from pootle_fs.matcher import FSPathMatcher
from pootle_fs.resources import FSProjectResources
from pootle_fs.delegate import fs_finder, fs_matcher, fs_resources
from pootle_fs.state import ProjectFSState

from .plugin import GitPlugin


@provider(fs_plugins)
def git_plugin_provider(**kwargs):
    return dict(git=GitPlugin)


@getter(state, sender=GitPlugin)
def git_plugin_state_getter(**kwargs):
    return ProjectFSState


@getter(fs_resources, sender=GitPlugin)
def git_resources_getter(**kwargs):
    return FSProjectResources


@getter(fs_finder, sender=GitPlugin)
def git_finder_getter(**kwargs):
    return TranslationFileFinder


@getter(fs_matcher, sender=GitPlugin)
def git_matcher_getter(**kwargs):
    return FSPathMatcher
