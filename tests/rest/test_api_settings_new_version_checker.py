import json
import falcon
from mock import Mock, PropertyMock, patch
from ddt import ddt, data, unpack
from tests import RestTestBase
from monitorrent.rest.settings_new_version_checker import SettingsNewVersionChecker
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker


@ddt
class SettingsNewVersionCheckerTest(RestTestBase):
    @data((True, True, 3600),
          (False, True, 3600),
          (True, True, 7200),
          (False, True, 7200),
          (True, False, 3600),
          (False, False, 3600),
          (True, False, 7200),
          (False, False, 7200))
    @unpack
    def test_is_new_version_checker_enabled(self, include_prerelease, enabled, interval):
        with patch('monitorrent.settings_manager.SettingsManager.new_version_check_interval',
                   new_callable=PropertyMock) as new_version_check_interval_mock:
            new_version_check_interval_mock.return_value = interval

            settings_manager = SettingsManager()
            get_is_new_version_checker_enabled_mock = Mock(return_value=enabled)
            get_new_version_check_include_prerelease_mock = Mock(return_value=include_prerelease)
            settings_manager.get_is_new_version_checker_enabled = get_is_new_version_checker_enabled_mock
            settings_manager.get_new_version_check_include_prerelease = get_new_version_check_include_prerelease_mock

            new_version_checker = NewVersionChecker(Mock(), False)
            new_version_checker.execute = Mock()

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            body = self.simulate_request("/api/settings/new_version_checker", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

            result = json.loads(body)

            expected = {'include_prerelease': include_prerelease, 'enabled': enabled, 'interval': interval}
            self.assertEqual(result, expected)

            get_is_new_version_checker_enabled_mock.assert_called_once_with()
            get_new_version_check_include_prerelease_mock.assert_called_once_with()
            new_version_check_interval_mock.assert_called_once_with()

    @data(
        (True, False, 3600, True, False, 3600),
        (False, False, 3600, False, False, 3600),
        (None, False, 3600, False, False, 3600),
        (True, False, 3600, True, False, 3600),
        (False, False, 3600, False, False, 3600),
        (None, False, 3600, False, False, 3600),
        (True, False, 7200, True, False, 7200),
        (False, False, 7200, False, False, 7200),
        (None, False, 7200, False, False, 7200),
        (True, True, 7200, True, True, 7200),
        (False, True, 7200, False, True, 7200),
        (None, True, 7200, False, True, 7200),
        (True, True, None, True, True, 4000),
        (False, True, None, False, True, 4000),
        (None, True, None, False, True, 4000),
        (True, None, 7200, True, True, 7200),
        (False, None, 7200, False, True, 7200),
        (None, None, 7200, False, True, 7200),
    )
    @unpack
    def test_patch_test(self, patch_include_prerelease, patch_enabled, patch_interval, update_include_prerelease, update_enabled, update_interval):
        with patch('monitorrent.settings_manager.SettingsManager.new_version_check_interval',
                   new_callable=PropertyMock) as new_version_check_interval_mock:

            new_version_check_interval_mock.return_value = 4000

            settings_manager = SettingsManager()
            settings_manager.get_new_version_check_include_prerelease = Mock(return_value=False)
            settings_manager.set_new_version_check_include_prerelease = Mock()
            settings_manager.get_is_new_version_checker_enabled = Mock(return_value=True)
            settings_manager.set_is_new_version_checker_enabled = Mock()
            settings_manager.new_version_check_interval = PropertyMock(return_value=3600)

            new_version_checker = NewVersionChecker(Mock(), False)
            update_mock = Mock()
            new_version_checker.update = update_mock

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            request = dict()
            if patch_include_prerelease is not None:
                request['include_prerelease'] = patch_include_prerelease
            if patch_enabled is not None:
                request['enabled'] = patch_enabled
            if patch_interval is not None:
                request['interval'] = patch_interval
            self.simulate_request('/api/settings/new_version_checker', method="PATCH", body=json.dumps(request))

            self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

            update_mock.assert_called_once_with(update_include_prerelease, update_enabled, update_interval)

    @data({'enabled': 'True'},
          {'enabled': '1'},
          {'enabled': 'abcd'},
          {'include_prerelease': 'True'},
          {'include_prerelease': '1'},
          {'include_prerelease': 'abcd'},
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

            new_version_checker = NewVersionChecker(Mock(), False)
            new_version_checker.execute = Mock()

            settings_new_version_checker = SettingsNewVersionChecker(settings_manager, new_version_checker)
            self.api.add_route('/api/settings/new_version_checker', settings_new_version_checker)

            self.simulate_request("/api/settings/new_version_checker", method="PATCH", body=json.dumps(body) if body else None)

            self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
