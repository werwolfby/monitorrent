import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsAuthenticationTest(RestTestBase):
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
