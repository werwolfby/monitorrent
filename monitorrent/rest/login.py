from builtins import object
import falcon
from monitorrent.rest import MonitorrentRequest, MonitorrentResponse, AuthMiddleware, no_auth
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
@no_auth
class Login(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_post(self, req, resp):
        """
        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        body = req.json
        if body is None or 'password' not in body:
            raise falcon.HTTPBadRequest('WrongPassword', 'password is not specified')
        password = body['password']
        if password != self.settings_manager.get_password():
            raise falcon.HTTPUnauthorized('WrongPassword', 'password is not correct', None)
        AuthMiddleware.authenticate(resp)


# noinspection PyUnusedLocal, PyMethodMayBeStatic
class Logout(object):
    def on_post(self, req, resp):
        AuthMiddleware.logout(resp)
        resp.status = falcon.HTTP_NO_CONTENT
