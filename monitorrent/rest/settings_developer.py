from builtins import object
import falcon
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsDeveloper(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'is_developer_mode': self.settings_manager.get_is_developer_mode()}

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        is_developer_mode = req.json.get('is_developer_mode')
        if is_developer_mode is None or not isinstance(is_developer_mode, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"is_developer_mode" is required and have to be bool')

        self.settings_manager.set_is_developer_mode(is_developer_mode)
        resp.status = falcon.HTTP_NO_CONTENT
