# coding=utf-8
from mock import patch
from monitorrent.plugins.trackers import LoginResult, TrackerSettings, CloudflareChallengeSolverSettings
from monitorrent.plugins.trackers.rutracker import RutrackerPlugin, RutrackerLoginFailedException, RutrackerTopic
from monitorrent.db import DBSession
from tests import use_vcr, DbTestCase
from tests.plugins.trackers import TrackerSettingsMock
from tests.plugins.trackers.rutracker.rutracker_helper import RutrackerHelper


class RutrackerPluginTest(DbTestCase):
    def setUp(self):
        super(RutrackerPluginTest, self).setUp()
        cloudflare_challenge_solver_settings = CloudflareChallengeSolverSettings(False, 10000, False, False, 0)
        self.tracker_settings = TrackerSettingsMock(10, None, cloudflare_challenge_solver_settings)
        self.plugin = RutrackerPlugin()
        self.plugin.init(self.tracker_settings)
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
            parsed_url['original_name'], u'Безумный Макс: Дорога ярости в 3Д / Mad Max: Fury Road 3D '
                                         u'(Джордж Миллер / George Miller) [2015, Боевик, Фантастика, '
                                         u'Приключения, BDRip-AVC] Half OverUnder / Вертикальная анаморфная стереопара')

    @use_vcr
    def test_parse_not_found_url(self):
        parsed_url = self.plugin.parse_url(u'http://rutracker.org/forum/viewtopic.php?t=5018612')
        self.assertIsNone(parsed_url)

    @use_vcr
    def test_login_verify_fail(self):
        self.assertFalse(self.plugin.verify())
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        credentials = {'username': '', 'password': ''}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.CredentialsNotSpecified)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': self.helper.fake_login, 'password': self.helper.fake_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)
        self.assertFalse(self.plugin.verify())

    @use_vcr
    def test_login_verify_success(self):
        credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Ok)
        self.assertTrue(self.plugin.verify())

    def test_login_failed_exceptions_1(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=RutrackerLoginFailedException(1, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=RutrackerLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_prepare_request(self):
        cookies = {'bb_session': '1-4301487-ZdJuaHIfHpaJiVn8VPKU-0-1461694123-1461698647-4135149312-1'}
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'get_cookies', result=cookies):
            url = 'http://rutracker.org/forum/viewtopic.php?t=5062041'
            request = self.plugin._prepare_request(RutrackerTopic(url=url))
            self.assertIsNotNone(request)
            self.assertEqual(request.headers['referer'], url)
            self.assertEqual(request.headers['host'], 'rutracker.org')
            self.assertEqual(request.url, 'https://rutracker.org/forum/dl.php?t=5062041')

    def test_prepare_request_sends_cloudflare_headers(self):
        # cf_clearance is issued for one User-Agent and is worthless without it
        self.plugin.tracker.setup(self.helper.fake_uid, self.helper.fake_bb_data,
                                  headers={'User-Agent': 'test-agent'},
                                  cookies={'cf_clearance': 'test-clearance'})

        url = 'http://rutracker.org/forum/viewtopic.php?t=5062041'
        request = self.plugin._prepare_request(RutrackerTopic(url=url))

        self.assertEqual(request.headers['User-Agent'], 'test-agent')
        # request-specific headers must still win over the stored ones
        self.assertEqual(request.headers['referer'], url)
        self.assertEqual(request.headers['host'], 'rutracker.org')

    @patch('monitorrent.plugins.trackers.rutracker.RutrackerPlugin.login')
    def test_update_credentials_stores_cloudflare_cookies(self, login):
        # cookies and headers must survive a round trip through the credentials API
        login.return_value = LoginResult.Ok

        self.plugin.update_credentials({
            'username': self.helper.fake_login,
            'password': self.helper.fake_password,
            'cookies': '{"cf_clearance": "test-clearance"}',
            'headers': '{"User-Agent": "test-agent"}',
        })

        credentials = self.plugin.get_credentials()
        self.assertEqual(credentials['cookies'], '{"cf_clearance": "test-clearance"}')
        self.assertEqual(credentials['headers'], '{"User-Agent": "test-agent"}')

    def test_credentials_accept_bare_cookie_value(self):
        # the one cookie worth pasting is cf_clearance — that is what Cloudflare checks
        from monitorrent.plugins.trackers.rutracker import parse_cookies_field

        self.assertEqual(parse_cookies_field('abc123'), {'cf_clearance': 'abc123'})
        self.assertEqual(parse_cookies_field('  abc123  '), {'cf_clearance': 'abc123'})
        self.assertEqual(parse_cookies_field('{"cf_clearance": "abc123"}'), {'cf_clearance': 'abc123'})
        self.assertIsNone(parse_cookies_field(''))
        self.assertIsNone(parse_cookies_field(None))

    def test_credentials_accept_bare_user_agent(self):
        # same shape for the User-Agent, and no invented default
        from monitorrent.plugins.trackers.rutracker import parse_headers_field

        self.assertEqual(parse_headers_field('My Browser 1.0'), {'User-Agent': 'My Browser 1.0'})
        self.assertEqual(parse_headers_field('{"User-Agent": "My Browser 1.0"}'), {'User-Agent': 'My Browser 1.0'})
        self.assertIsNone(parse_headers_field(''))
        self.assertIsNone(parse_headers_field(None))

    @patch('monitorrent.plugins.trackers.rutracker.RutrackerTracker.verify')
    def test_verify_restores_stored_cookies_and_headers(self, tracker_verify):
        # everything after login runs on the credentials restored here
        tracker_verify.return_value = True
        self.plugin.update_credentials({
            'username': self.helper.fake_login,
            'password': self.helper.fake_password,
            'cookies': '{"cf_clearance": "test-clearance"}',
            'headers': 'test-agent',
        })
        with DBSession() as db:
            cred = db.query(self.plugin.credentials_class).first()
            cred.uid = self.helper.fake_uid
            cred.bb_data = self.helper.fake_bb_data

        self.plugin.verify()

        self.assertEqual(self.plugin.tracker.cookies.get('cf_clearance'), 'test-clearance')
        self.assertEqual(self.plugin.tracker.headers.get('User-Agent'), 'test-agent')

    @patch('monitorrent.plugins.trackers.rutracker.RutrackerTracker.login')
    def test_login_requires_user_agent_with_clearance(self, tracker_login):
        # cf_clearance without its User-Agent is refused by Cloudflare anyway
        result = self.plugin.update_credentials({
            'username': self.helper.fake_login,
            'password': self.helper.fake_password,
            'cookies': 'test-clearance',
            'headers': '',
        })

        self.assertEqual(result, LoginResult.CredentialsNotSpecified)
        self.assertFalse(tracker_login.called)
