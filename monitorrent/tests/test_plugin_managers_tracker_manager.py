import os
from mock import Mock, MagicMock, patch
from monitorrent.tests import TestCase
from monitorrent.plugins.trackers import TrackerPluginBase, TrackerPluginWithCredentialsBase
from monitorrent.plugin_managers import TrackersManager


class TrackersManagerTest(TestCase):
    TRACKER1_PLUGIN_NAME = 'tracker1.com'
    TRACKER2_PLUGIN_NAME = 'tracker2.com'

    class Tracker1(TrackerPluginBase):
        def parse_url(self, url):
            pass

        def can_parse_url(self, url):
            pass

        def _prepare_request(self, topic):
            pass

    class Tracker2(TrackerPluginWithCredentialsBase):
        def parse_url(self, url):
            pass

        def can_parse_url(self, url):
            pass

        def _prepare_request(self, topic):
            pass

        def login(self):
            pass

        def verify(self):
            pass

    def test_get_settings(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        self.assertIsNone(trackers_manager.get_settings(self.TRACKER1_PLUGIN_NAME))

        credentials2 = {'login': 'username'}
        get_credentials_mock = MagicMock(return_value=credentials2)
        tracker2.get_credentials = get_credentials_mock

        self.assertEqual(trackers_manager.get_settings(self.TRACKER2_PLUGIN_NAME), credentials2)

        get_credentials_mock.assert_called_with()

    def test_set_settings(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        credentials1 = {'login': 'username'}
        self.assertFalse(trackers_manager.set_settings(self.TRACKER1_PLUGIN_NAME, credentials1))

        credentials2 = {'login': 'username', 'password': 'password'}
        update_credentials_mock2 = MagicMock()
        tracker2.update_credentials = update_credentials_mock2

        self.assertTrue(trackers_manager.set_settings(self.TRACKER2_PLUGIN_NAME, credentials2))

        update_credentials_mock2.assert_called_with(credentials2)
