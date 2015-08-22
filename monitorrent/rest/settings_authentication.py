import falcon
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsAuthentication(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'is_authentication_enabled': self.settings_manager.get_is_authentication_enabled()}

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        if 'password' not in req.json or 'is_authentication_enabled' not in req.json:
            raise falcon.HTTPBadRequest('ParamRequired',
                                        '"password" and "is_authentication_enabled" properties are required')

        password = req.json['password']
        is_authentication_enabled = req.json['is_authentication_enabled']
        if not isinstance(is_authentication_enabled, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"is_authentication_enabled" have to be bool')

        if password != self.settings_manager.get_password():
            raise falcon.HTTPBadRequest('WrongValue', '"password" is wrong')
        self.settings_manager.set_is_authentication_enabled(is_authentication_enabled)
        resp.status = falcon.HTTP_NO_CONTENT
