import json
import falcon
from ddt import ddt, data, unpack
from mock import Mock
from tests import RestTestBase
from monitorrent.rest.settings_notify_on import SettingsNotifyOn


@ddt
class SettingsNewVersionCheckerTest(RestTestBase):
    def test_get_notify_on(self):
        settings_manager = Mock()
        settings_manager.get_external_notifications_levels = Mock(return_value=['1', '2', '3'])

        # noinspection PyTypeChecker
        settings_notify_on = SettingsNotifyOn(settings_manager)

        self.api.add_route('/api/settings/notify_on', settings_notify_on)
        body = self.simulate_request('/api/settings/notify_on', decode='utf-8')

        assert self.srmock.status == falcon.HTTP_OK
        assert 'application/json' in self.srmock.headers_dict['Content-Type']

        result = json.loads(body)

        assert result == ['1', '2', '3']

    def test_set_notify_on_success(self):
        settings_manager = Mock()
        settings_manager.get_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.get_existing_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.set_external_notifications_levels = Mock()

        # noinspection PyTypeChecker
        settings_notify_on = SettingsNotifyOn(settings_manager)

        self.api.add_route('/api/settings/notify_on', settings_notify_on)
        self.simulate_request('/api/settings/notify_on', decode='utf-8', method="PUT", body=json.dumps(['1', '2']))

        assert self.srmock.status == falcon.HTTP_NO_CONTENT

        settings_manager.set_external_notifications_levels.assert_called_once_with(['1', '2'])

    def test_set_notify_on_empty_body_bad_request(self):
        settings_manager = Mock()
        settings_manager.get_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.get_existing_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.set_external_notifications_levels = Mock()

        # noinspection PyTypeChecker
        settings_notify_on = SettingsNotifyOn(settings_manager)

        self.api.add_route('/api/settings/notify_on', settings_notify_on)
        body = self.simulate_request('/api/settings/notify_on', decode='utf-8', method="PUT")

        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

        result = json.loads(body)

        assert result['title'] == 'BodyRequired'

        settings_manager.assert_not_called()

    @data(
        ([1, 2, 3],),
        ({'level_1': True, 'level_2': False},)
    )
    @unpack
    def test_set_notify_on_wrong_body_bad_request(self, levels):
        settings_manager = Mock()
        settings_manager.get_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.get_existing_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.set_external_notifications_levels = Mock()

        # noinspection PyTypeChecker
        settings_notify_on = SettingsNotifyOn(settings_manager)

        self.api.add_route('/api/settings/notify_on', settings_notify_on)
        body = self.simulate_request('/api/settings/notify_on', decode='utf-8', method="PUT",
                                     body=json.dumps(levels))

        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

        result = json.loads(body)

        assert result['title'] == 'ArrayOfStringExpected'

        settings_manager.assert_not_called()

    def test_set_notify_on_unknown_levels_bad_request(self):
        settings_manager = Mock()
        settings_manager.get_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.get_existing_external_notifications_levels = Mock(return_value=['1', '2', '3'])
        settings_manager.set_external_notifications_levels = Mock()

        # noinspection PyTypeChecker
        settings_notify_on = SettingsNotifyOn(settings_manager)

        self.api.add_route('/api/settings/notify_on', settings_notify_on)
        body = self.simulate_request('/api/settings/notify_on', decode='utf-8', method="PUT",
                                     body=json.dumps(['level_a', 'level_b', '1', '2']))

        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

        result = json.loads(body)

        assert result['title'] == 'UnknownLevels'
        assert 'level_a' in result['description']
        assert 'level_b' in result['description']

        settings_manager.assert_not_called()
