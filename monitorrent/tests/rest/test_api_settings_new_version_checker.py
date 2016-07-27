import json
import falcon
from mock import Mock, PropertyMock, patch, ANY
from ddt import ddt, data, unpack
from monitorrent.tests import RestTestBase
from monitorrent.rest.settings_new_version_checker import SettingsNewVersionChecker
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker


@ddt
class SettingsNewVersionCheckerTest(RestTestBase):
    @data((True, 3600),
          (True, 7200),
          (False, 3600),
          (False, 7200))
    @unpack
    def test_is_new_version_checker_enabled(self, value, interval):
        with patch('monitorrent.settings_manager.SettingsManager.new_version_check_interval',
                   new_callable=PropertyMock) as new_version_check_interval_mock:
            new_version_check_interval_mock.return_value = interval

            settings_manager = SettingsManager()
            get_is_new_version_checker_enabled = Mock(return_value=value)
            settings_manager.get_is_new_version_checker_enabled = get_is_new_version_checker_enabled

            new_version_checker = NewVersionChecker(False)
            new_version_checker.execute = Mock()

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            body = self.simulate_request("/api/settings/new_version_checker", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

            result = json.loads(body)

            self.assertEqual(result, {'enabled': value, 'interval': interval})

            get_is_new_version_checker_enabled.assert_called_once_with()
            new_version_check_interval_mock.assert_called_once_with()

    @data(
        (False, 3600, False, 3600),
        (False, 7200, False, 7200),
        (True, 7200, True, 7200),
        (True, None, True, 4000),
        (None, 7200, True, 7200),
    )
    @unpack
    def test_patch_test(self, patch_enabled, patch_interval, update_enabled, update_interval):
        with patch('monitorrent.settings_manager.SettingsManager.new_version_check_interval',
                   new_callable=PropertyMock) as new_version_check_interval_mock, \
                patch('monitorrent.new_version_checker.Timer') as TimerMock:

            new_version_check_interval_mock.return_value = 4000

            settings_manager = SettingsManager()
            get_is_new_version_checker_enabled = Mock(return_value=True)
            set_is_new_version_checker_enabled = Mock()

            settings_manager.get_is_new_version_checker_enabled = get_is_new_version_checker_enabled
            settings_manager.set_is_new_version_checker_enabled = set_is_new_version_checker_enabled
            settings_manager.new_version_check_interval = PropertyMock(return_value=3600)

            new_version_checker = NewVersionChecker(False)
            update_mock = Mock()
            new_version_checker.update = update_mock

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            request = dict()
            if patch_enabled is not None:
                request['enabled'] = patch_enabled
            if patch_interval is not None:
                request['interval'] = patch_interval
            self.simulate_request('/api/settings/new_version_checker', method="PATCH", body=json.dumps(request))

            self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

            update_mock.assert_called_once_with(update_enabled, update_interval)

    @data({'enabled': 'True'},
          {'enabled': '1'},
          {'enabled': 'abcd'},
          {'interval': '10'},
          {'interval': 'abcd'},
          None)
    def test_bad_request(self, body):
        with patch('monitorrent.settings_manager.SettingsManager.new_version_check_interval',
                   new_callable=PropertyMock) as new_version_check_interval_mock:
            new_version_check_interval_mock.return_value = 4000

            settings_manager = SettingsManager()
            get_is_new_version_checker_enabled = Mock()
            settings_manager.get_is_new_version_checker_enabled = get_is_new_version_checker_enabled

            new_version_checker = NewVersionChecker(False)
            new_version_checker.execute = Mock()

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            self.simulate_request("/api/settings/new_version_checker", method="PATCH", body=json.dumps(body) if body else None)

            self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
