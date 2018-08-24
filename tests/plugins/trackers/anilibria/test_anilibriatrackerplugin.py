# coding=utf-8
from unittest import TestCase
from monitorrent.plugins.trackers import  TrackerSettings
from monitorrent.plugins.trackers.anilibria import AnilibriaTvPlugin, AnilibriaTvTopic
from tests import use_vcr


class AnilibriaTrackerPluginTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10, None)
        self.plugin = AnilibriaTvPlugin()
        self.plugin.init(self.tracker_settings)
        self.urls_ok = [
            "https://www.anilibria.tv/release/inuyashiki.html",
            "https://anilibria.tv/release/inuyashiki.html"

        ]
        self.urls_fail = [
            "https://wwwanilibria.tv/release/inuyashiki.html",
            "https://rutracker.org/forum/viewtopic.php?t=5501844"
        ]

    def test_can_parse_url(self):
        for url in self.urls_ok:
            self.assertTrue(self.plugin.can_parse_url(url))

        for url in self.urls_fail:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        name = u"Inuyashiki / Инуяшики"
        for url in self.urls_ok:
            result = self.plugin.parse_url(url)
            self.assertEqual(result["original_name"], name)

    @use_vcr
    def test_prepare_request(self):
        request = self.plugin._prepare_request(AnilibriaTvTopic(url = "https://www.anilibria.tv/release/inuyashiki.html"))
        self.assertIsNotNone(request)
        self.assertEqual(request.url, "https://www.anilibria.tv/upload/torrents/4045.torrent")