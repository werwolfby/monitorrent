import falcon
import structlog

from monitorrent.new_version_checker import NewVersionChecker

log = structlog.get_logger()


# noinspection PyUnusedLocal
class NewVersion(object):
    def __init__(self, new_version_checker):
        """
        :type new_version_checker: NewVersionChecker
        """
        self.new_version_checker = new_version_checker

    def on_get(self, req, resp):
        try:
            resp.json = {'url': self.new_version_checker.new_version_url}
        except Exception as e:
            log.error("An error has occurred", exception=str(e))
            raise falcon.HTTPInternalServerError(title='A server has encountered an error', description=str(e))
