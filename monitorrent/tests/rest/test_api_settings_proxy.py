import json
import falcon
from mock import PropertyMock, MagicMock, patch
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.settings_proxy import SettingsProxyEnabled
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsProxyEnabledTest(RestTestBase):
    api_url = '/api/settings/proxy/enabled'

    @data(True, False)
    def test_get_is_proxy_enabled(self, value):
        settings_manager = SettingsManager()
        get_is_proxy_enabled_mock = MagicMock(return_value=value)
        settings_manager.get_is_proxy_enabled = get_is_proxy_enabled_mock
        settings_proxy_enabled_resource = SettingsProxyEnabled(settings_manager)
        self.api.add_route(self.api_url, settings_proxy_enabled_resource)

        body = self.simulate_request(self.api_url, decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'enabled': value})

        get_is_proxy_enabled_mock.assert_called_once_with()

    @data(True, False)
    def test_set_is_proxy_enabled(self, value):
        settings_manager = SettingsManager()
        set_is_proxy_enabled_mock = MagicMock()
        settings_manager.set_is_proxy_enabled = set_is_proxy_enabled_mock
        settings_proxy_enabled_resource = SettingsProxyEnabled(settings_manager)
        self.api.add_route(self.api_url, settings_proxy_enabled_resource)

        request = {'enabled': value}
        self.simulate_request(self.api_url, method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

        set_is_proxy_enabled_mock.assert_called_once_with(value)

    @data({'enabled': 'random_text'},
          {'enabled': 'True'},
          {'wrong_param': 'Value'},
          None)
    def test_bad_request(self, body):
        settings_manager = SettingsManager()
        settings_proxy_enabled_resource = SettingsProxyEnabled(settings_manager)
        self.api.add_route(self.api_url, settings_proxy_enabled_resource)

        self.simulate_request(self.api_url, method="PUT", body=json.dumps(body) if body else None)

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
