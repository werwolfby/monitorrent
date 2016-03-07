# coding=utf-8
from monitorrent.plugins.trackers import LoginResult, PluginSettings
from monitorrent.plugins.trackers.tapochek import TapochekNetPlugin
from monitorrent.tests import use_vcr, DbTestCase
from monitorrent.tests.plugins.trackers.tapochek.tapochektracker_helper import TapochekHelper


class TapochekPluginTest(DbTestCase):
    def setUp(self):
        super(TapochekPluginTest, self).setUp()
        self.plugin_settings = PluginSettings(10)
        self.plugin = TapochekNetPlugin()
        self.plugin.init(self.plugin_settings)
        self.helper = TapochekHelper()
        self.urls_to_check = [
            "http://tapochek.net/viewtopic.php?t=140574",
            "http://www.tapochek.net/viewtopic.php?t=140574"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        bad_urls = [
            "http://rutracker.com/forum/viewtopic.php?t=5062041",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.plugin.parse_url("http://tapochek.net/viewtopic.php?t=140574")
        self.assertEqual(
            parsed_url['original_name'], u'Железный человек 3 / Iron man 3 (Шейн Блэк) '
                                         u'[2013 г., фантастика, боевик, приключения, BDRemux 1080p]')

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
