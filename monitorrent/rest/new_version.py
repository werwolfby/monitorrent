from monitorrent.new_version_checker import NewVersionChecker


# noinspection PyUnusedLocal
class NewVersion(object):
    def __init__(self, new_version_checker):
        """
        :type new_version_checker: NewVersionChecker
        """
        self.new_version_checker = new_version_checker

    def on_get(self, req, resp):
        resp.json = {'url': self.new_version_checker.new_version_url}
