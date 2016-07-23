# coding=utf-8
from mock import patch, Mock
from unittest import TestCase
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.rutracker import RutrackerTracker, RutrackerLoginFailedException
from monitorrent.tests import use_vcr
from monitorrent.tests.plugins.trackers.rutracker.rutracker_helper import RutrackerHelper


class RutrackerTrackerTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10, None)
        self.tracker = RutrackerTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.helper = RutrackerHelper()
        self.urls_to_check = [
            "http://rutracker.org/forum/viewtopic.php?t=5062041",
            "http://www.rutracker.org/forum/viewtopic.php?t=5062041"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.tracker.can_parse_url(url))

        bad_urls = [
            "http://rutracker.com/forum/viewtopic.php?t=5062041",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.tracker.parse_url("http://rutracker.org/forum/viewtopic.php?t=5062041")
        self.assertEqual(
            parsed_url['original_name'], u'Бeзyмный Мaкс: Дoрoга яpоcти в 3Д / Mаd Mаx: Furу Rоad 3D '
                                         u'(Джoрдж Миллер / Geоrge Millеr) [2015, Боевик, Фантастика, '
                                         u'Приключения, BDrip-AVC] Half OverUnder / Вертикальная анаморфная стереопара')

    @use_vcr
    def test_parse_url_1(self):
        parsed_url = self.tracker.parse_url("http://rutracker.org/forum/viewtopic.php?t=5018611")
        self.assertEqual(parsed_url['original_name'],
                         u'Ганнибал / Hannibal / Сезон: 3 / Серии: 1-11 из 13 '
                         u'(Гильермо Наварро, Майкл Раймер, Дэвид Слэйд) [2015, детектив, криминал, драма, HDTVRip] '
                         u'MVO (Sony Sci Fi) + Original + Subs (Rus, Eng)')

    @use_vcr
    def test_parse_wrong_url(self):
        parsed_url = self.tracker.parse_url('http://not.rutracker.ogre/forum/viewtopic.php?t=5018611')
        self.assertFalse(parsed_url)
        # special case for not existing topic
        parsed_url = self.tracker.parse_url('http://rutracker.org/forum/viewtopic.php?t=50186110')
        self.assertFalse(parsed_url)

    @use_vcr
    def test_login_failed(self):
        with self.assertRaises(RutrackerLoginFailedException) as e:
            self.tracker.login(self.helper.fake_login, self.helper.fake_password)
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, 'Invalid login or password')

    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_failed_cookie(self, post):
        login_result = Mock()
        login_result.url = 'http://rutracker.org/forum/index.php'
        post.return_value = login_result
        with self.assertRaises(RutrackerLoginFailedException) as e:
            self.tracker.login(self.helper.fake_login, self.helper.fake_password)
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to retrieve cookie')

    @use_vcr
    def test_login(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertEqual(self.tracker.bb_data, self.helper.real_bb_data)
        self.assertEqual(self.tracker.uid, self.helper.real_uid)

    @use_vcr
    def test_verify(self):
        self.tracker.login(self.helper.real_login, self.helper.real_password)
        self.assertTrue(self.tracker.verify())

    def test_verify_failed(self):
        self.tracker.setup(None, None)
        self.assertFalse(self.tracker.verify())

        self.tracker.setup('1-23-45', None)
        self.assertFalse(self.tracker.verify())

    def test_get_cookies(self):
        self.assertFalse(self.tracker.get_cookies())
        self.tracker = RutrackerTracker(self.helper.real_uid, self.helper.real_bb_data)
        self.tracker.tracker_settings = self.tracker_settings
        self.assertEqual(self.tracker.get_cookies()['bb_data'], self.helper.real_bb_data)

    def test_get_id(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_id(url), "5062041")

    def test_get_download_url(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_download_url(url), "http://dl.rutracker.org/forum/dl.php?t=5062041")

    def test_get_download_url_error(self):
        self.assertIsNone(self.tracker.get_download_url("http://not.rutracker.org/forum/viewtopic.php?t=5062041"))
