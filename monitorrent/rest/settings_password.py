from builtins import object
import falcon
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsPassword(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        if 'old_password' not in req.json or 'new_password' not in req.json:
            raise falcon.HTTPBadRequest('ParamRequired', '"old_password" and "new_password" properties are required')

        old_password = req.json['old_password']
        new_password = req.json['new_password']

        if old_password != self.settings_manager.get_password():
            raise falcon.HTTPBadRequest('WrongValue', '"old_password" is wrong')
        self.settings_manager.set_password(new_password)
        resp.status = falcon.HTTP_NO_CONTENT
