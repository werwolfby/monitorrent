# coding=utf-8
from mock import patch, Mock
from unittest import TestCase
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.freetorrents import FreeTorrentsOrgTracker, FreeTorrentsLoginFailedException
from monitorrent.tests import use_vcr
from monitorrent.tests.plugins.trackers.freetorrents.freetorrentstracker_helper import FreeTorrentsHelper


class FreeTorrentsTrackerTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10, None)
        self.tracker = FreeTorrentsOrgTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.helper = FreeTorrentsHelper()
        self.urls_to_check = [
            "http://free-torrents.org/forum/viewtopic.php?t=207456",
            "http://www.free-torrents.org/forum/viewtopic.php?t=207456"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.tracker.can_parse_url(url))

        bad_urls = [
            "http://free-torrents.com/forum/viewtopic.php?t=207456",
            "http://beltracker.org/forum/viewtopic.php?t=207456"
        ]
        for url in bad_urls:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.tracker.parse_url("http://free-torrents.org/forum/viewtopic.php?t=207456")
        self.assertEqual(
            parsed_url['original_name'], u'Мистер Робот / Mr. Robot [Сезон 1 (1-9 из 10)]'
                                         u'[2015, Драма, криминал, WEB-DLRip] [MVO (LostFilm)]')

    @use_vcr
    def test_parse_wrong_url(self):
        parsed_url = self.tracker.parse_url('http://free-torrents.ogre/forum/viewtopic.php?t=207456')
        self.assertFalse(parsed_url)
        # special case for not existing topic
        parsed_url = self.tracker.parse_url('http://free-torrents.org/forum/viewtopic.php?t=2074560')
        self.assertFalse(parsed_url)

    @use_vcr
    def test_login_failed(self):
        with self.assertRaises(FreeTorrentsLoginFailedException) as e:
            self.tracker.login(self.helper.fake_login, self.helper.fake_password)
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, 'Invalid login or password')

    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_failed_cookie(self, post):
        login_result = Mock()
        login_result.url = 'http://rutracker.org/forum/index.php'
        post.return_value = login_result
        with self.assertRaises(FreeTorrentsLoginFailedException) as e:
            self.tracker.login(self.helper.fake_login, self.helper.fake_password)
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to retrieve cookie')

    @use_vcr
    def test_login(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertEqual(self.tracker.bbe_data, self.helper.real_bbe_data)
        self.assertEqual(self.tracker.uid, self.helper.real_uid)

    @use_vcr
    def test_verify(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertTrue(self.tracker.verify())

    def test_verify_failed(self):
        self.tracker.setup(None, None)
        self.assertFalse(self.tracker.verify())

        self.tracker.setup('a%E4%E5%E6%E7', None)
        self.assertFalse(self.tracker.verify())

    def test_get_cookies(self):
        self.assertFalse(self.tracker.get_cookies())
        self.tracker = FreeTorrentsOrgTracker(self.helper.real_uid, self.helper.real_bbe_data)
        self.tracker.tracker_settings = self.tracker_settings
        self.assertEqual(self.tracker.get_cookies()['bbe_data'], self.helper.real_bbe_data)

    @use_vcr
    def test_get_download_url(self):
        self.tracker = FreeTorrentsOrgTracker(self.helper.real_uid, self.helper.real_bbe_data)
        self.tracker.tracker_settings = self.tracker_settings
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_download_url(url), 'http://dl.free-torrents.org/forum/dl.php?id=152988')
