import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.settings_developer import SettingsDeveloper
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsDeveloperTest(RestTestBase):
    @data(True, False)
    def test_is_developer_mode(self, value):
        settings_manager = SettingsManager()
        get_is_developer_mode_mock = MagicMock(return_value=value)
        settings_manager.get_is_developer_mode = get_is_developer_mode_mock
        settings_developer_resource = SettingsDeveloper(settings_manager)
        self.api.add_route('/api/settings/developer', settings_developer_resource)

        body = self.simulate_request("/api/settings/developer", decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'is_developer_mode': value})

        get_is_developer_mode_mock.assert_called_once_with()

    @data(True, False)
    def test_set_is_developer_mode(self, value):
        settings_manager = SettingsManager()
        set_is_developer_mode_mock = MagicMock()
        settings_manager.set_is_developer_mode = set_is_developer_mode_mock
        settings_developer_resource = SettingsDeveloper(settings_manager)
        self.api.add_route('/api/settings/developer', settings_developer_resource)

        request = {'is_developer_mode': value}
        self.simulate_request("/api/settings/developer", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

        set_is_developer_mode_mock.assert_called_once_with(value)

    @data({'is_developer_mode': 'random_text'},
          {'is_developer_mode': 'True'},
          {'wrong_param': 'Value'},
          None)
    def test_bad_request(self, body):
        settings_manager = SettingsManager()
        settings_developer_resource = SettingsDeveloper(settings_manager)
        self.api.add_route('/api/settings/developer', settings_developer_resource)

        self.simulate_request("/api/settings/developer", method="PUT", body=json.dumps(body) if body else None)

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)