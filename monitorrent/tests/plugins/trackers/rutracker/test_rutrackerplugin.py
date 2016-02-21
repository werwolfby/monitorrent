# coding=utf-8
from monitorrent.plugins.trackers import LoginResult
from monitorrent.plugins.trackers.rutracker import RutrackerPlugin
from monitorrent.tests import use_vcr, DbTestCase
from monitorrent.tests.plugins.trackers.rutracker.rutracker_helper import RutrackerHelper


class RutrackerPluginTest(DbTestCase):
    def setUp(self):
        super(RutrackerPluginTest, self).setUp()
        self.plugin = RutrackerPlugin()
        self.helper = RutrackerHelper()
        self.urls_to_check = [
            "http://rutracker.org/forum/viewtopic.php?t=5062041",
            "http://www.rutracker.org/forum/viewtopic.php?t=5062041"
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
        parsed_url = self.plugin.parse_url("http://rutracker.org/forum/viewtopic.php?t=5062041")
        self.assertEqual(
            parsed_url['original_name'], u'Бeзyмный Мaкс: Дoрoга яpоcти в 3Д / Mаd Mаx: Furу Rоad 3D '
                                         u'(Джoрдж Миллер / Geоrge Millеr) [2015, Боевик, Фантастика, '
                                         u'Приключения, BDrip-AVC] Half OverUnder / Вертикальная анаморфная стереопара')

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
