# coding=utf-8
from unittest import TestCase
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.anilibria import AnilibriaTvTracker
from tests import use_vcr

class AnilibriaTrackerTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10, 30000, None)
        self.tracker = AnilibriaTvTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.urls_to_parse = [
            "https://www.anilibria.tv/release/inuyashiki.html",
            "https://anilibria.tv/release/inuyashiki.html"
        ]
        self.urls_not_to_parse = [
            "https://wwwanilibria.tv/release/inuyashiki.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        ]
        self.urls_parse_failed = [
            "https://wwwanilibria.tv/release/inuyashiki.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "https://www.anilibria.tv/release/notfound.html",
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_parse:
            self.assertTrue(self.tracker.can_parse_url(url))

        for url in self.urls_not_to_parse:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        url = "https://www.anilibria.tv/release/inuyashiki.html"
        result = self.tracker.parse_url(url)
        name = u"Инуяшики / Inuyashiki"
        self.assertEqual(result["original_name"], name)
        self.assertEqual(result["format_list"], ['HDTV-Rip 720p'])

    @use_vcr
    def test_parse_wrong_url(self):
        for url in self.urls_parse_failed:
            self.assertFalse(self.tracker.parse_url(url))

    @use_vcr
    def test_get_download_url(self):
        self.assertEqual(self.tracker.get_download_url("https://www.anilibria.tv/release/inuyashiki.html", None),
                         "https://www.anilibria.tv/upload/torrents/4045.torrent")
        self.assertEqual(self.tracker.get_download_url("https://www.anilibria.tv/release/seishun-buta-yarou-wa-bunny-girl-senpai-no-yume-wo-minai.html", ""),
                         "https://www.anilibria.tv/upload/torrents/6029.torrent")
        self.assertEqual(self.tracker.get_download_url("https://www.anilibria.tv/release/seishun-buta-yarou-wa-bunny-girl-senpai-no-yume-wo-minai.html", "HDTVRip 720p"),
                         "https://www.anilibria.tv/upload/torrents/6028.torrent")
        self.assertEqual(self.tracker.get_download_url("https://www.anilibria.tv/release/seishun-buta-yarou-wa-bunny-girl-senpai-no-yume-wo-minai.html", "HDTVRip 1080p"),
                         "https://www.anilibria.tv/upload/torrents/6029.torrent")

    @use_vcr
    def test_get_download_url_error(self):
        for url in self.urls_parse_failed:
            self.assertIsNone(self.tracker.get_download_url(url, None))
