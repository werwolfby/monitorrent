from future import standard_library
standard_library.install_aliases()
#!/usr/bin/env python
# coding=utf-8
from unittest import TestCase
from urllib.parse import urlparse
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.unionpeer import UnionpeerOrgTracker
from monitorrent.tests import use_vcr


class UnionpeerTrackerTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10)
        self.tracker = UnionpeerOrgTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.urls_to_parse = [
            "http://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://www.unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "https://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        ]

    def test_can_parse_url(self):
        urls_not_to_parse = [
            "http://rutracker.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
        ]
        for url in self.urls_to_parse:
            self.assertTrue(self.tracker.can_parse_url(url))

        for url in urls_not_to_parse:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        url = "http://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        result = self.tracker.parse_url(url)
        name = u'Звёздные Войны: Войны Клонов (Сезон 4, DVD) / Star Wars: The Clone Wars / Сезон: 4 / ' \
               u'Серии: 8 из 22 (Дэйв Филони | Dave Filoni) [2011, Анимация, фантасткика, боевик, DVD5 (Custom)] Dub ' \
               u'+ Rus Sub'
        self.assertEqual(result["original_name"], name)

    @use_vcr
    def test_get_hash(self):
        url = "http://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        result = self.tracker.get_hash(url)
        self.assertEqual(result, "A3019CE458B52AFFD3E36FDF71101D16F46930E8")

    @use_vcr
    def test_get_id(self):
        for url in self.urls_to_parse:
            parsed_url = urlparse(url)
            self.assertEqual(self.tracker.get_id(parsed_url.path), "1177708")

    @use_vcr
    def test_get_download_url(self):
        for url in self.urls_to_parse:
            self.assertEqual(self.tracker.get_download_url(url), "http://unionpeer.org/dl.php?t=1177708")

    @use_vcr
    def test_get_title(self):
        title = "faketitle"
        complex_title = self.tracker._get_title(title)
        self.assertEqual(title, complex_title["original_name"])
