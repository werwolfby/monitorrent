import json
import falcon
from mock import PropertyMock, patch
from ddt import ddt, data
from tests import RestTestBase
from monitorrent.rest.settings_logs import SettingsLogs
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsLogsTest(RestTestBase):
    remove_logs_interval_property = 'monitorrent.settings_manager.SettingsManager.remove_logs_interval'

    @data(10, 11, 12, 13)
    def test_is_developer_mode(self, value):
        with patch(self.remove_logs_interval_property, new_callable=PropertyMock) as remove_logs_interval_mock:
            remove_logs_interval_mock.return_value = value
            settings_manager = SettingsManager()
            settings_logs_resource = SettingsLogs(settings_manager)
            self.api.add_route('/api/settings/logs', settings_logs_resource)

            body = self.simulate_request("/api/settings/logs", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

            result = json.loads(body)

            self.assertEqual(result, {'interval': value})

            remove_logs_interval_mock.assert_called_once_with()

    @data(10, 20, 15)
    def test_set_is_developer_mode(self, value):
        with patch(self.remove_logs_interval_property, new_callable=PropertyMock) as remove_logs_interval_mock:
            remove_logs_interval_mock.return_value = value
            settings_manager = SettingsManager()
            settings_logs_resource = SettingsLogs(settings_manager)
            self.api.add_route('/api/settings/logs', settings_logs_resource)

            request = {'interval': value}
            self.simulate_request("/api/settings/logs", method="PUT", body=json.dumps(request))

            self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

            remove_logs_interval_mock.assert_called_once_with(value)

    @data({'interval': 'random_text'},
          {'interval': '10'},
          {'wrong_param': '10'},
          None)
    def test_bad_request(self, body):
        settings_manager = SettingsManager()
        settings_developer_resource = SettingsLogs(settings_manager)
        self.api.add_route('/api/settings/logs', settings_developer_resource)

        self.simulate_request("/api/settings/logs", method="PUT", body=json.dumps(body) if body else None)

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)