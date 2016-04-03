from future import standard_library
standard_library.install_aliases()
import json
import falcon
import http.cookies
import dateutil.parser
from datetime import datetime
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest import AuthMiddleware
from monitorrent.rest.login import Login, Logout
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
        cookie = http.cookies.SimpleCookie()
        cookie.load(set_cookie)
        self.assertEqual(1, len(cookie))
        jwt_morsel = list(cookie.values())[0]
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

    def test_logout_success(self):
        self.api.add_route(self.test_route, Logout())
        self.simulate_request(self.test_route, method="POST", headers={'Cookie': self.get_cookie()})

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)
        set_cookie = self.srmock.headers_dict['set-cookie']
        cookie = http.cookies.SimpleCookie()
        cookie.load(set_cookie)
        self.assertEqual(1, len(cookie))
        jwt_morsel = list(cookie.values())[0]
        self.assertEqual(AuthMiddleware.cookie_name, jwt_morsel.key)
        self.assertEqual("", jwt_morsel.value)
        expires = dateutil.parser.parse(jwt_morsel['expires'], ignoretz=True)
        self.assertEqual(datetime.utcfromtimestamp(0), expires)

    def test_logout_unauthorized(self):
        self.api.add_route(self.test_route, Logout())
        self.simulate_request(self.test_route, method="POST", headers={'Cookie': self.get_cookie(True)})

        self.assertEqual(self.srmock.status, falcon.HTTP_UNAUTHORIZED)
