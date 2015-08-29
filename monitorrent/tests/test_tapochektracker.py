# coding=utf-8
from unittest import TestCase
from monitorrent.plugins.trackers.tapochek import TapochekNetTracker, TapochekLoginFailedException
from monitorrent.tests import use_vcr
from monitorrent.tests.tapochektracker_helper import TapochekHelper


class TapochekTrackerTest(TestCase):
    def setUp(self):
        self.tracker = TapochekNetTracker()
        self.helper = TapochekHelper()
        self.urls_to_check = [
            "http://tapochek.net/viewtopic.php?t=140574",
            "http://www.tapochek.net/viewtopic.php?t=140574"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.tracker.can_parse_url(url))

        bad_urls = [
            "http://tapochek.com/viewtopic.php?t=140574",
            "http://beltracker.net/viewtopic.php?t=140574",
        ]
        for url in bad_urls:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.tracker.parse_url("http://tapochek.net/viewtopic.php?t=140574")
        self.assertEqual(
            parsed_url['original_name'], u'Железный человек 3 / Iron man 3 (Шейн Блэк) '
                                         u'[2013 г., фантастика, боевик, приключения, BDRemux 1080p]')

    @use_vcr
    def test_login_failed(self):
        with self.assertRaises(TapochekLoginFailedException) as e:
            self.tracker.login(self.helper.fake_login, self.helper.fake_password)
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, 'Invalid login or password')

    @use_vcr
    def test_login(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertEqual(self.tracker.bb_data, self.helper.real_bb_data)
        self.assertEqual(self.tracker.uid, self.helper.real_uid)

    @use_vcr
    def test_verify(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertTrue(self.tracker.verify())

    def test_get_cookies(self):
        self.assertFalse(self.tracker.get_cookies())
        self.tracker = TapochekNetTracker(self.helper.real_uid, self.helper.real_bb_data)
        self.assertEqual(self.tracker.get_cookies()['bb_data'], self.helper.real_bb_data)

    @use_vcr
    def test_get_hash(self):
        self.tracker = TapochekNetTracker(self.helper.real_uid, self.helper.real_bb_data)
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_hash(url),
                             '9E6D08A214168D8DB8511378DC9DD0E0102A2691')

    def test_get_id(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_id(url), "140574")

    @use_vcr
    def test_get_download_url(self):
        self.tracker = TapochekNetTracker(self.helper.real_uid, self.helper.real_bb_data)
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_download_url(url),
                             'http://tapochek.net/download.php?id=94914')
