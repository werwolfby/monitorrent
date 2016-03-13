# coding=utf-8
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.freetorrents import FreeTorrentsOrgPlugin
from monitorrent.tests import DbTestCase, use_vcr
from monitorrent.tests.plugins.trackers.freetorrents.freetorrentstracker_helper import FreeTorrentsHelper


class FreeTorrentsPluginTest(DbTestCase):
    def setUp(self):
        super(FreeTorrentsPluginTest, self).setUp()
        plugin_settings = TrackerSettings(10)
        self.plugin = FreeTorrentsOrgPlugin()
        self.plugin.init(plugin_settings)
        self.helper = FreeTorrentsHelper()
        self.urls_to_check = [
            "http://free-torrents.org/forum/viewtopic.php?t=207456",
            "http://www.free-torrents.org/forum/viewtopic.php?t=207456"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        bad_urls = [
            "http://free-torrents.com/forum/viewtopic.php?t=207456",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.plugin.parse_url("http://free-torrents.org/forum/viewtopic.php?t=207456")
        self.assertEqual(
            parsed_url['original_name'], u'Мистер Робот / Mr. Robot [Сезон 1 (1-9 из 10)]'
                                         u'[2015, Драма, криминал, WEB-DLRip] [MVO (LostFilm)]')

    @use_vcr
    def test_login_verify(self):
        self.assertFalse(self.plugin.verify())
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        self.plugin.update_credentials({'username': '', 'password': ''})
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        self.plugin.update_credentials({'username': self.helper.fake_login, 'password': self.helper.fake_password})
        self.assertEqual(self.plugin.login(), LoginResult.IncorrentLoginPassword)

        self.plugin.update_credentials({'username': self.helper.real_login, 'password': self.helper.real_password})

        self.assertEqual(LoginResult.Ok, self.plugin.login())
        self.assertTrue(self.plugin.verify())
