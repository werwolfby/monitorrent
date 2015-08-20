import json
import falcon
from falcon.testing import TestBase
from mock import MagicMock
from ddt import ddt, data
from monitorrent.rest import create_api
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsAuthenticationTest(TestBase):
    def setUp(self):
        """Initializer, unittest-style"""
        super(SettingsAuthenticationTest, self).setUp()
        self.api = create_api()

    @data(True, False)
    def test_is_authentication_enabled(self, value):
        settings_manager = SettingsManager()
        settings_manager.get_is_authentication_enabled = MagicMock(return_value=value)
        settings_authentication_resource = SettingsAuthentication(settings_manager)
        self.api.add_route('/api/settings/authentication', settings_authentication_resource)

        body = self.simulate_request("/api/settings/authentication")

        self.assertEqual(self.srmock.status, falcon.HTTP_200)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertEqual(result, {'is_authentication_enabled': value})
