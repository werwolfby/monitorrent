from builtins import object
import falcon
import six
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsLogs(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'interval': self.settings_manager.remove_logs_interval}

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        interval = req.json.get('interval')
        if interval is None or not isinstance(interval, six.integer_types):
            raise falcon.HTTPBadRequest('WrongValue', '"interval" is required and have to be int')

        self.settings_manager.remove_logs_interval = interval
        resp.status = falcon.HTTP_NO_CONTENT
