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

    def test_check_connection(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        self.assertFalse(trackers_manager.check_connection(self.TRACKER1_PLUGIN_NAME))

        verify_mock = MagicMock(return_value=True)
        tracker2.verify = verify_mock

        self.assertTrue(trackers_manager.check_connection(self.TRACKER2_PLUGIN_NAME))

        verify_mock.assert_called_with()

    def test_prepare_add_topic_1(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        parsed_url = {'display_name': "Some Name / Translated Name"}
        prepare_add_topic_mock1 = MagicMock(return_value=parsed_url)
        tracker1.prepare_add_topic = prepare_add_topic_mock1
        result = trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNotNone(result)

        prepare_add_topic_mock1.assert_called_with(('http://tracker.com/1/'))

        self.assertEqual(result, {'form': TrackerPluginBase.topic_form, 'settings': parsed_url})

    def test_prepare_add_topic_2(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        prepare_add_topic_mock1 = MagicMock(return_value=None)
        tracker1.prepare_add_topic = prepare_add_topic_mock1

        parsed_url = {'display_name': "Some Name / Translated Name"}
        prepare_add_topic_mock2 = MagicMock(return_value=parsed_url)
        tracker2.prepare_add_topic = prepare_add_topic_mock2

        result = trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNotNone(result)

        prepare_add_topic_mock1.assert_called_with('http://tracker.com/1/')
        prepare_add_topic_mock2.assert_called_with('http://tracker.com/1/')

        self.assertEqual(result, {'form': TrackerPluginBase.topic_form, 'settings': parsed_url})

    def test_prepare_add_topic_3(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        prepare_add_topic_mock1 = MagicMock(return_value=None)
        tracker1.prepare_add_topic = prepare_add_topic_mock1

        prepare_add_topic_mock2 = MagicMock(return_value=None)
        tracker2.prepare_add_topic = prepare_add_topic_mock2

        result = trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNone(result)

        prepare_add_topic_mock1.assert_called_with('http://tracker.com/1/')
        prepare_add_topic_mock2.assert_called_with('http://tracker.com/1/')

    def test_add_topic_1(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        can_parse_url_mock1 = MagicMock(return_value=True)
        add_topic_mock1 = MagicMock(return_value=True)
        tracker1.can_parse_url = can_parse_url_mock1
        tracker1.add_topic = add_topic_mock1

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertTrue(trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_called_with(url, params)

    def test_add_topic_2(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        can_parse_url_mock1 = MagicMock(return_value=False)
        add_topic_mock1 = MagicMock(return_value=False)
        tracker1.can_parse_url = can_parse_url_mock1
        tracker1.add_topic = add_topic_mock1

        can_parse_url_mock2 = MagicMock(return_value=True)
        add_topic_mock2 = MagicMock(return_value=True)
        tracker2.can_parse_url = can_parse_url_mock2
        tracker2.add_topic = add_topic_mock2

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertTrue(trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_not_called()

        can_parse_url_mock2.assert_called_with(url)
        add_topic_mock2.assert_called_with(url, params)

    def test_add_topic_3(self):
        tracker1 = self.Tracker1()
        tracker2 = self.Tracker2()
        trackers_manager = TrackersManager({
            self.TRACKER1_PLUGIN_NAME: tracker1,
            self.TRACKER2_PLUGIN_NAME: tracker2,
        })

        can_parse_url_mock1 = MagicMock(return_value=False)
        add_topic_mock1 = MagicMock(return_value=False)
        tracker1.can_parse_url = can_parse_url_mock1
        tracker1.add_topic = add_topic_mock1

        can_parse_url_mock2 = MagicMock(return_value=False)
        add_topic_mock2 = MagicMock(return_value=False)
        tracker2.can_parse_url = can_parse_url_mock2
        tracker2.add_topic = add_topic_mock2

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertFalse(trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_not_called()

        can_parse_url_mock2.assert_called_with(url)
        add_topic_mock2.assert_not_called()
