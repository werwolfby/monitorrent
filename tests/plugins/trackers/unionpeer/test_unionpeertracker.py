# coding=utf-8
from future import standard_library
standard_library.install_aliases()
#!/usr/bin/env python
from unittest import TestCase
from urllib.parse import urlparse
from monitorrent.plugins.trackers import TrackerSettings, CloudflareChallengeSolverSettings
from monitorrent.plugins.trackers.unionpeer import UnionpeerOrgTracker
from tests import use_vcr


class UnionpeerTrackerTest(TestCase):
    def setUp(self):
        cloudflare_challenge_solver_settings = CloudflareChallengeSolverSettings(False, 10000, False, False, 0)
        self.tracker_settings = TrackerSettings(10, None, cloudflare_challenge_solver_settings)
        self.tracker = UnionpeerOrgTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.urls_to_parse = [
            "http://unionpeer.org/topic/1177708",
            "http://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://www.unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "https://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        ]
        self.urls_not_to_parse = [
            "http://rutracker.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
        ]
        self.urls_parse_failed = [
            "http://rutracker.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://unionpeer.org/topic1/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_parse:
            self.assertTrue(self.tracker.can_parse_url(url))

        for url in self.urls_not_to_parse:
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
    def test_parse_wrong_url(self):
        for url in self.urls_parse_failed:
            parsed_url = self.tracker.parse_url(url)
            self.assertFalse(parsed_url)
        # special case for not existing topic
        self.assertFalse(self.tracker.parse_url("http://unionpeer.org/topic/2177708"))

    @use_vcr
    def test_get_id(self):
        for url in self.urls_to_parse:
            self.assertEqual(self.tracker.get_id(url), "1177708")

    def test_get_download_url(self):
        for url in self.urls_to_parse:
            self.assertEqual(self.tracker.get_download_url(url), "http://unionpeer.org/dl.php?t=1177708")

    def test_get_download_url_error(self):
        for url in self.urls_parse_failed:
            self.assertIsNone(self.tracker.get_download_url(url))

    @use_vcr
    def test_get_title(self):
        title = "faketitle"
        complex_title = self.tracker._get_title(title)
        self.assertEqual(title, complex_title["original_name"])
