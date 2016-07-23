from builtins import object
import falcon
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsProxyEnabled(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'enabled': self.settings_manager.get_is_proxy_enabled()}

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        enabled = req.json.get('enabled')
        if enabled is None or not isinstance(enabled, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"enabled" is required and have to be bool')

        self.settings_manager.set_is_proxy_enabled(enabled)
        resp.status = falcon.HTTP_NO_CONTENT


# noinspection PyUnusedLocal
class SettingsProxy(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        key = req.get_param('key')
        url = self.settings_manager.get_proxy(key)
        if url is None or url == "":
            raise falcon.HTTPNotFound()
        resp.json = {'url': url}

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        key = req.get_param('key')
        url = req.json.get('url')
        if url is None or url == "":
            raise falcon.HTTPBadRequest('WrongValue', '"url" is required and have to be not empty string')

        self.settings_manager.set_proxy(key, url)
        resp.status = falcon.HTTP_NO_CONTENT

    def on_delete(self, req, resp):
        key = req.get_param('key')
        self.settings_manager.set_proxy(key, None)
        resp.status = falcon.HTTP_NO_CONTENT
