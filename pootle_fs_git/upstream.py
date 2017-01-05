

class GithubUpstreamFS(object):

    def __init__(self, context):
        self.context = context

    @property
    def repo_uri(self):
        return self.context.fs_url

    @property
    def url(self):
        user, repo = self.repo_uri.split(":")[1].split("/")
        return "https://github.com/%s/%s" % (user, repo)
