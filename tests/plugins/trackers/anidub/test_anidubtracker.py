# coding=utf-8
from unittest import TestCase

from ddt import data, ddt, unpack
from mock import Mock, patch

from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.anidub import AnidubTracker, AnidubLoginFailedException
from tests import use_vcr

from tests.plugins.trackers.anidub.anidub_helper import AnidubHelper


# helper = AnidubHelper.login('realusername', 'realpassword')
helper = AnidubHelper()


@ddt
class AnidubTrackerTest(TestCase):
    def setUp(self):
        super(AnidubTrackerTest, self).setUp()
        self.tracker_settings = TrackerSettings(10, None)
        self.tracker = AnidubTracker()
        self.tracker.tracker_settings = self.tracker_settings

    @data(("https://tr.anidub.com/anime_tv/full/9465-ray-v-seryh-tonah-grisaia-no-rakuen-01-iz-111sp.html", True),
          ("https://tr.anidub.com/manga/9228-chernyy-kot-black-cat-glavy-001-187-iz-187.html", True),
          ("https://tr.anidub.com/?newsid=8827", True),
          ("https://anidub/invalid.url", False))
    @unpack
    def test_can_parse_url(self, url, result):
        self.assertEqual(self.tracker.can_parse_url(url), result)

    @use_vcr
    @data(
        ("https://tr.anidub.com/?newsid=492",
         u"Пожиратель душ / Soul Eater [51 из 51]",
         ['TV (720p)', 'BD (720p)', 'HWP', 'PSP'])
    )
    @unpack
    def test_parse_url(self, url, name, format_list):
        result = self.tracker.parse_url(url)
        self.assertIsNotNone(result)
        self.assertEqual(result['original_name'], name)
        self.assertEqual(result['format_list'], format_list)

    @data("https://invalid.url", "https://tr.anidub.com/anime_tv/100-nothing.html")
    @use_vcr
    def test_parse_invalid_url(self, url):
        self.assertIsNone(self.tracker.parse_url(url))

    @use_vcr
    def test_login_failed(self):
        with self.assertRaises(AnidubLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, 'Invalid login or password')

    @patch("monitorrent.plugins.trackers.anidub.Session.post")
    def test_login_failed_cookie(self, post):
        login_result = Mock()
        login_result.text = '...<a href="https://tr.anidub.com/index.php?action=logout">...'
        post.return_value = login_result
        with self.assertRaises(AnidubLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to retrieve cookies')

    @helper.use_vcr()
    def test_login(self):
        self.tracker.login(helper.real_login, helper.real_password)
        self.assertTrue((self.tracker.dle_uid == helper.real_dle_uid) or (self.tracker.dle_uid == helper.fake_dle_uid))

    def test_verify_false(self):
        self.tracker.dle_pwd = None
        self.tracker.dle_uid = None
        self.assertFalse(self.tracker.verify())

    @use_vcr
    def test_verify_fail(self):
        self.tracker.dle_uid = "abcd123456"
        self.tracker.dle_pwd = "abcd123456"
        self.assertFalse(self.tracker.verify())

    @helper.use_vcr()
    def test_verify(self):
        self.tracker.dle_uid = helper.real_dle_uid
        self.tracker.dle_pwd = helper.real_dle_pwd
        self.assertTrue(self.tracker.verify())

    @helper.use_vcr()
    def test_get_download_url(self):
        self.tracker.dle_pwd = helper.real_dle_pwd
        self.tracker.dle_uid = helper.real_dle_uid
        result = self.tracker.get_download_url("https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01"
                                               "-51-of-512008-720r.html", "BD (720p)")
        self.assertEqual(result, "https://tr.anidub.com/engine/download.php?id=641")
        result = self.tracker.get_download_url("https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01"
                                               "-51-of-512008-720r.html", "Unknown Format")
        self.assertIsNone(result)
