import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from tests import RestTestBase
from monitorrent.rest.settings_password import SettingsPassword
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsPasswordTest(RestTestBase):
    @staticmethod
    def _get_settings_manager(password):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value=password)
        settings_manager.set_password = MagicMock()
        return settings_manager

    @data('password', 's3cured1p@$$!')
    def test_set_password_successful(self, password):
        settings_manager = self._get_settings_manager(password)
        settings_authentication_resource = SettingsPassword(settings_manager)
        self.api.add_route('/api/settings/password', settings_authentication_resource)

        request = {'old_password': password, 'new_password': 'new_password'}
        self.simulate_request("/api/settings/password", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    @data('password', 's3cured1p@$$!')
    def test_set_password_failed(self, password):
        settings_manager = self._get_settings_manager(password + '_secret')
        settings_authentication_resource = SettingsPassword(settings_manager)
        self.api.add_route('/api/settings/password', settings_authentication_resource)

        request = {'old_password': password, 'new_password': 'new_password'}
        self.simulate_request("/api/settings/password", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_set_password_empty_request(self):
        settings_manager = self._get_settings_manager("monitorrent")
        settings_authentication_resource = SettingsPassword(settings_manager)
        self.api.add_route(self.test_route, settings_authentication_resource)

        self.simulate_request(self.test_route, method="PUT")

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    @data({'old_password': 'monitorrent'},
          {'new_password': 'monitorrent'},
          {'random_property': 'random'})
    def test_set_password_bad_request(self, body):
        settings_manager = self._get_settings_manager("monitorrent")
        settings_authentication_resource = SettingsPassword(settings_manager)
        self.api.add_route(self.test_route, settings_authentication_resource)

        self.simulate_request(self.test_route, method="PUT", body=json.dumps(body))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
