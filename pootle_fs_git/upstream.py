# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle_fs.utils import FSPlugin


class UpstreamProvider(object):

    def __init__(self, project, location=None):
        self.project = project
        self.location = location


class GithubUpstream(UpstreamProvider):

    @cached_property
    def plugin(self):
        return FSPlugin(self.project)

    @property
    def fs_url(self):
        return self.plugin.fs_url

    @property
    def fs_path(self):
        return self.fs_url.split(":")[1]

    @property
    def upstream_url(self):
        return "https://github.com/%s" % self.fs_path

    @property
    def latest_hash(self):
        self.plugin.latest_hash[:10]

    @property
    def revision_url(self):
        revision_url = (
            "%s/tree/%s"
            % (self.fs_url, self.latest_hash))
        if not self.location:
            return revision_url
        return (
            "%s%s#L%s"
            % (revision_url,
               self.location.split(":")[0],
               self.location.split(":")[1]))

    @property
    def context_data(self):
        return dict(
            upstream_url=self.upstream_url,
            fs_path=self.fs_path,
            revision_url=self.revision_url,
            lastest_hash=self.latest_hash)
