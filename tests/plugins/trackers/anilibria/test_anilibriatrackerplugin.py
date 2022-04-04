# coding=utf-8
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.anilibria import AnilibriaTvPlugin, AnilibriaTvTopic
from tests import use_vcr, DbTestCase


class AnilibriaTrackerPluginTest(DbTestCase):
    def setUp(self):
        super(AnilibriaTrackerPluginTest, self).setUp()
        self.tracker_settings = TrackerSettings(10, 30000, None)
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
        name = u"Инуяшики / Inuyashiki"
        for url in self.urls_ok:
            result = self.plugin.parse_url(url)
            self.assertEqual(result["original_name"], name)

    @use_vcr
    def test_prepare_request(self):
        request = self.plugin._prepare_request(AnilibriaTvTopic(url="https://www.anilibria.tv/release/inuyashiki.html"))
        self.assertIsNotNone(request)
        self.assertEqual(request.url, "https://www.anilibria.tv/upload/torrents/4045.torrent")

    @use_vcr()
    def test_add_topic(self):
        params = {
            'display_name': u"Этот глупый свин не понимает мечту девочки-зайки / Seishun Buta Yarou wa Bunny Girl "
                            u"Senpai no Yume wo Minai",
            'format': "HDTVRip 1080p"
        }
        url = "https://www.anilibria.tv/release/seishun-buta-yarou-wa-bunny-girl-senpai-no-yume-wo-minai.html"
        self.assertTrue(self.plugin.add_topic(url, params))
        topic = self.plugin.get_topic(1)
        self.assertIsNotNone(topic)
        self.assertEqual(url, topic['url'])
        self.assertEqual(self.plugin.topic_form[0]['content'][1]['options'], ['HDTVRip 1080p', 'HDTVRip 720p'])
        self.assertEqual(topic['format_list'], 'HDTVRip 1080p,HDTVRip 720p')
        self.assertEqual(params['display_name'], topic['display_name'])
        self.assertEqual(params['format'], topic['format'])
