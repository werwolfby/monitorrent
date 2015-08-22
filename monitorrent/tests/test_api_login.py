import json
import falcon
import Cookie
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest import AuthMiddleware
from monitorrent.rest.login import Login
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsAuthenticationTest(RestTestBase):
    def setUp(self, disable_auth=False):
        super(SettingsAuthenticationTest, self).setUp(disable_auth)

    @data('password', 's3cured1p@$$!')
    def test_login_success(self, password):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value=password)
        settings_authentication_resource = Login(settings_manager)
        self.api.add_route(self.test_route, settings_authentication_resource)

        self.simulate_request(self.test_route, method='POST', body=json.dumps({'password': password}))

        self.assertEqual(self.srmock.status, falcon.HTTP_200)
        set_cookie = self.srmock.headers_dict['set-cookie']
        cookie = Cookie.SimpleCookie()
        cookie.load(set_cookie)
        self.assertEqual(1, len(cookie))
        jwt_morsel = cookie.values()[0]
        self.assertEqual(AuthMiddleware.cookie_name, jwt_morsel.key)
        self.assertEqual(self.auth_token_verified, jwt_morsel.value)

    def test_login_bad_request(self):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value='monitorrent')
        settings_authentication_resource = Login(settings_manager)
        self.api.add_route(self.test_route, settings_authentication_resource)

        self.simulate_request(self.test_route, method='POST', body=json.dumps({}))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_login_unauthorized(self):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value='monitorrent')
        settings_authentication_resource = Login(settings_manager)
        self.api.add_route(self.test_route, settings_authentication_resource)

        self.simulate_request(self.test_route, method='POST', body=json.dumps({'password': 'MonITorrenT'}))

        self.assertEqual(self.srmock.status, falcon.HTTP_UNAUTHORIZED)
