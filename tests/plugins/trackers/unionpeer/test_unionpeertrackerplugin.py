# coding=utf-8
from unittest import TestCase
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.unionpeer import UnionpeerOrgPlugin, UnionpeerOrgTopic
from tests import use_vcr


class UnionpeerTrackerPluginTest(TestCase):
    def setUp(self):
        self.tracker_settings = TrackerSettings(10, None)
        self.plugin = UnionpeerOrgPlugin()
        self.plugin.init(self.tracker_settings)
        self.urls_to_check = [
            "http://unionpeer.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html"
        ]

    def test_can_parse_url(self):
        urls_not_to_parse = [
            "http://rutracker.org/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
            "http://unionpeer/topic/1177708-zvezdnie-voyni-voyni-klonov-star-wars-the-clone-wars.html",
        ]
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        for url in urls_not_to_parse:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        name = u'Звёздные Войны: Войны Клонов (Сезон 4, DVD) / Star Wars: The Clone Wars / Сезон: 4 / ' \
               u'Серии: 8 из 22 (Дэйв Филони | Dave Filoni) [2011, Анимация, фантасткика, боевик, DVD5 (Custom)] Dub ' \
               u'+ Rus Sub'
        for url in self.urls_to_check:
            result = self.plugin.parse_url(url)
            self.assertEqual(result["original_name"], name)

    def test_prepare_request(self):
        for url in self.urls_to_check:
            topic = UnionpeerOrgTopic()
            topic.url = url
            self.assertEqual("http://unionpeer.org/dl.php?t=1177708", self.plugin._prepare_request(topic))\
