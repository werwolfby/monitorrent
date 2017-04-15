# coding=utf-8
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.tapochek import TapochekNetPlugin, TapochekLoginFailedException, TapochekNetTopic
from tests import use_vcr, DbTestCase
from tests.plugins.trackers.tapochek.tapochektracker_helper import TapochekHelper
from mock import patch, Mock, ANY


class TapochekPluginTest(DbTestCase):
    def setUp(self):
        super(TapochekPluginTest, self).setUp()
        self.tracker_settings = TrackerSettings(10, None)
        self.plugin = TapochekNetPlugin()
        self.plugin.init(self.tracker_settings)
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

        credentials = {'username': '', 'password': ''}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.CredentialsNotSpecified)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': self.helper.fake_login, 'password': self.helper.fake_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Ok)
        self.assertTrue(self.plugin.verify())

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=TapochekLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_failed_exceptions_173_with_engine(self):
        exception = TapochekLoginFailedException(173, 'Invalid login or password')
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.plugin.update_credentials(credentials)

            engine_mock = Mock()
            self.assertEqual(self.plugin.login(engine_mock), LoginResult.Unknown)
            engine_mock.failed.assert_called_once_with("Can't login", TapochekLoginFailedException, exception, ANY)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.plugin.update_credentials(credentials)
            self.assertEqual(self.plugin.login(), LoginResult.Unknown)

    def test_login_unexpected_exceptions_with_engine(self):
        exception = Exception()
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.plugin.update_credentials(credentials)

            engine_mock = Mock()
            self.assertEqual(self.plugin.login(engine_mock), LoginResult.Unknown)
            engine_mock.failed.assert_called_once_with("Can't login", Exception, exception, ANY)

    def test_prepare_request(self):
        cookies = {'bb_data': self.helper.real_bb_data}
        download_url = "http://tapochek.net/download.php?id=110717"
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'get_cookies', result=cookies),\
                patch.object(self.plugin.tracker, 'get_download_url', return_value=download_url):
            url = 'http://tapochek.net/viewtopic.php?t=174801'
            request = self.plugin._prepare_request(TapochekNetTopic(url=url))
            self.assertIsNotNone(request)
            self.assertEqual(request.headers['referer'], url)
            self.assertEqual(request.headers['host'], 'tapochek.net')
            self.assertEqual(request.url, 'http://tapochek.net/download.php?id=110717')
