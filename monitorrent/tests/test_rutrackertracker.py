# coding=utf-8
from unittest import TestCase
from monitorrent.plugins.trackers.rutracker import RutrackerTracker, RutrackerLoginFailedException
from monitorrent.tests import use_vcr


class RutrackerTrackerTest(TestCase):
    def setUp(self):
        self.tracker = RutrackerTracker()
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

    # TODO the tests requiring login will fail due to captcha restrictions
    # @use_vcr
    # def test_login_failed(self):
    #     with self.assertRaises(RutrackerLoginFailedException) as e:
    #         self.tracker.login("asd", "qwe")
    #     self.assertEqual(e.exception.code, 1)
    #     self.assertEqual(e.exception.message, 'Invalid login or password')

    # @use_vcr
    # def test_verify_failed(self):
    #     tracker = RutrackerTracker("fake", "qwe")
    #     self.assertFalse(tracker.verify())

    # @use_vcr
    # def test_get_hash(self):
    #     for url in self.urls_to_check:
    #         self.assertEqual(self.tracker.get_hash(url), "")
    def test_get_id(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_id(url), "5062041")

    def test_get_download_url(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_download_url(url), "http://dl.rutracker.org/forum/dl.php?t=5062041")
