# coding=utf-8
from ddt import data, unpack, ddt
from mock import patch
from monitorrent.plugins.trackers import TrackerSettings, LoginResult
from monitorrent.plugins.trackers.anidub import AnidubPlugin, AnidubLoginFailedException, AnidubTopic
from tests import DbTestCase, use_vcr
from tests.plugins.trackers.anidub.anidub_helper import AnidubHelper

# helper = AnidubHelper.login('realusername', 'realpassword')
helper = AnidubHelper()


@ddt
class AnidubPluginTest(DbTestCase):
    def setUp(self):
        super(AnidubPluginTest, self).setUp()
        self.tracker_settings = TrackerSettings(10, None)
        self.plugin = AnidubPlugin()
        self.plugin.init(self.tracker_settings)

    @data(
        ("https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html", True),
        ("https://online.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html", False),
        ("https://tr.anidub.ru/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html", False),
        ("https://tr.anidub.com/index.php?newsid=9020", True),
        ("https://tr.anidub.com/?newsid=9020", True)
    )
    @unpack
    def test_can_parse_url(self, url, result):
        self.assertEqual(self.plugin.can_parse_url(url), result)

    @use_vcr()
    @data(
        ("https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html",
         u"Пожиратель душ / Soul Eater [51 из 51]",
         ['TV (720p)', 'BD (720p)', 'HWP', 'PSP'])
    )
    @unpack
    def test_parse_url(self, url, name, format_list):
        parsed_url = self.plugin.parse_url(url)
        self.assertIsNotNone(parsed_url)
        self.assertEqual(parsed_url['original_name'], name)
        self.assertEqual(parsed_url['format_list'], format_list)

    @use_vcr()
    @data("https://tr.anidub.com/anime_tv/full/100-move-along.html", "http://invalid.url")
    def test_parse_not_found_url(self, url):
        self.assertIsNone(self.plugin.parse_url(url))

    @helper.use_vcr()
    def test_login_verify(self):
        self.assertFalse(self.plugin.verify())
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        credentials = {'username': '', 'password': ''}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.CredentialsNotSpecified)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': helper.fake_login, 'password': helper.fake_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': helper.real_login, 'password': helper.real_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Ok)
        self.assertTrue(self.plugin.verify())

    def test_login_failed_exceptions_1(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=AnidubLoginFailedException(1, 'Invalid login or password')):
            credentials = {'username': helper.real_login, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=AnidubLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': helper.real_login, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': helper.real_login, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    @helper.use_vcr()
    def test_prepare_request(self):
        self.plugin.tracker.dle_uid = helper.real_dle_uid
        self.plugin.tracker.dle_pwd = helper.real_dle_pwd
        url = "https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html"
        request = self.plugin._prepare_request(AnidubTopic(url=url, format='BD (720p)'))
        self.assertIsNotNone(request)
        self.assertEqual(request.url, "https://tr.anidub.com/engine/download.php?id=641")
        request = self.plugin._prepare_request(AnidubTopic(url=url, format='Some Invalid Format'))
        self.assertIsNone(request)

    @use_vcr()
    @data(
        ("https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html",
         False,
         u"Пожиратель душ / Soul Eater [51 из 51]",
         'TV (720p)',
         ['TV (720p)', 'BD (720p)', 'HWP', 'PSP']),
        ("https://invalid.url",
         True,
         None,
         None,
         None)
    )
    @unpack
    def test_prepare_add_topic(self, url, fail_expected, name, default_format, format_list):
        result = self.plugin.prepare_add_topic(url)
        if fail_expected:
            self.assertIsNone(result)
        else:
            self.assertIsNotNone(result)
            self.assertEqual(result['display_name'], name)
            self.assertEqual(result['format'], default_format)
            self.assertEqual(self.plugin.topic_form[0]['content'][1]['options'], format_list)

    @helper.use_vcr()
    def test_add_topic(self):
        params = {
            'display_name': u"Пожиратель душ / Soul Eater [51 из 51]",
            'format': "BD (720p)"
        }
        url = "https://tr.anidub.com/anime_tv/full/492-pozhiratel-dush-soul-eater-01-51-of-512008-720r.html"
        self.assertTrue(self.plugin.add_topic(url, params))
        topic = self.plugin.get_topic(1)
        self.assertIsNotNone(topic)
        self.assertEqual(url, topic['url'])
        self.assertEqual(self.plugin.topic_form[0]['content'][1]['options'], ['TV (720p)', 'BD (720p)', 'HWP', 'PSP'])
        self.assertEqual(topic['format_list'], 'TV (720p),BD (720p),HWP,PSP')
        self.assertEqual(params['display_name'], topic['display_name'])
        self.assertEqual(params['format'], topic['format'])

    def test_get_topic_not_exist(self):
        topic = self.plugin.get_topic(100500)
        self.assertIsNone(topic)
