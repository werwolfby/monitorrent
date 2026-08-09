# coding=utf-8
from mock import patch, Mock
from unittest import TestCase

from monitorrent.plugins.trackers import CloudflareChallengeSolverSettings
from monitorrent.plugins.trackers.rutracker import RutrackerTracker, RutrackerLoginFailedException
from tests import use_vcr
from tests.plugins.trackers import TrackerSettingsMock
from tests.plugins.trackers.rutracker.rutracker_helper import RutrackerHelper

helper = RutrackerHelper()


class RutrackerTrackerTest(TestCase):
    def setUp(self):
        cloudflare_challenge_solver_settings = CloudflareChallengeSolverSettings(False, 10000, False, False, 0)
        self.tracker_settings = TrackerSettingsMock(10, None, cloudflare_challenge_solver_settings)
        self.tracker = RutrackerTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.urls_to_check = [
            "http://rutracker.org/forum/viewtopic.php?t=5062041",
            "http://www.rutracker.org/forum/viewtopic.php?t=5062041"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.tracker.can_parse_url(url))

        bad_urls = [
            "http://rutracker.com/forum/viewtopic.php?t=5062041",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.tracker.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.tracker.parse_url("http://rutracker.org/forum/viewtopic.php?t=5062041")
        self.assertEqual(
            parsed_url['original_name'], u'Бeзyмный Мaкс: Дoрoга яpоcти в 3Д / Mаd Mаx: Furу Rоad 3D '
                                         u'(Джoрдж Миллер / Geоrge Millеr) [2015, Боевик, Фантастика, '
                                         u'Приключения, BDrip-AVC] Half OverUnder / Вертикальная анаморфная стереопара')

    @use_vcr
    def test_parse_url_1(self):
        parsed_url = self.tracker.parse_url("https://rutracker.org/forum/viewtopic.php?t=5018611")
        self.assertEqual(parsed_url['original_name'],
                         u'Ганнибал / Hannibal / Сезон: 3 / Серии: 1-13 из 13 '
                         u'(Гильермо Наварро, Майкл Раймер, Дэвид Слэйд) '
                         u'[2015, США, детектив, криминал, драма, HDTVRip] '
                         u'MVO (Sony Sci Fi) + Original + Subs (Rus, Eng)')

    @use_vcr
    def test_parse_wrong_url(self):
        parsed_url = self.tracker.parse_url('http://not.rutracker.ogre/forum/viewtopic.php?t=5018611')
        self.assertFalse(parsed_url)
        # special case for not existing topic
        parsed_url = self.tracker.parse_url('http://rutracker.org/forum/viewtopic.php?t=50186110')
        self.assertFalse(parsed_url)

    @use_vcr
    def test_login_failed(self):
        with self.assertRaises(RutrackerLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, 'Invalid login or password')

    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_failed_cookie(self, post):
        login_result = Mock()
        login_result.url = 'http://rutracker.org/forum/index.php'
        post.return_value = login_result
        with self.assertRaises(RutrackerLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to retrieve cookie')

    @helper.use_vcr
    def test_login(self):
        self.tracker.login(helper.real_login, helper.real_password)
        self.assertEqual(self.tracker.bb_data, helper.real_bb_data)
        self.assertEqual(self.tracker.uid, helper.real_uid)

    @helper.use_vcr
    def test_verify(self):
        self.tracker.login(helper.real_login, helper.real_password)
        self.assertTrue(self.tracker.verify())

    def test_verify_failed(self):
        self.tracker.setup(None, None)
        self.assertFalse(self.tracker.verify())

        self.tracker.setup('1-23-45', None)
        self.assertFalse(self.tracker.verify())

    def test_get_cookies(self):
        self.assertFalse(self.tracker.get_cookies())
        self.tracker = RutrackerTracker(uid=helper.fake_uid, bb_data=helper.fake_bb_data)
        self.tracker.tracker_settings = self.tracker_settings
        self.assertEqual(self.tracker.get_cookies()['bb_session'], helper.fake_bb_data)

    @patch('monitorrent.plugins.trackers.rutracker.requests.get')
    def test_verify_failed_on_cloudflare_challenge(self, get):
        # cloudflare answers a protected page with 403 and without redirecting
        challenge_response = Mock()
        challenge_response.url = self.tracker.profile_page
        challenge_response.status_code = 403
        get.return_value = challenge_response

        self.tracker.setup(helper.fake_uid, helper.fake_bb_data)

        self.assertFalse(self.tracker.verify())

    @patch('monitorrent.plugins.trackers.rutracker.requests.get')
    def test_verify_success_requires_ok_status(self, get):
        ok_response = Mock()
        ok_response.url = self.tracker.profile_page
        ok_response.status_code = 200
        get.return_value = ok_response

        self.tracker.setup(helper.fake_uid, helper.fake_bb_data)

        self.assertTrue(self.tracker.verify())

    def test_get_cookies_keeps_cloudflare_cookies(self):
        # cloudflare hands out cf_clearance, and every later request needs it
        self.tracker = RutrackerTracker(uid=helper.fake_uid, bb_data=helper.fake_bb_data,
                                        cookies={'cf_clearance': 'test-clearance'})
        self.tracker.tracker_settings = self.tracker_settings

        cookies = self.tracker.get_cookies()

        self.assertEqual(cookies['bb_session'], helper.fake_bb_data)
        self.assertEqual(cookies['cf_clearance'], 'test-clearance')

    @patch('monitorrent.plugins.trackers.rutracker.update_headers_and_cookies_mixin')
    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_checks_challenge_on_protected_page(self, post, mixin):
        # the challenge check has to look at a page Cloudflare actually guards
        mixin.return_value = ({}, {})
        login_result = Mock()
        login_result.url = 'https://rutracker.org/forum/index.php'
        post.return_value = login_result

        try:
            self.tracker.login(helper.fake_login, helper.fake_password)
        except RutrackerLoginFailedException:
            pass

        self.assertTrue(mixin.called)
        checked_url = mixin.call_args[0][1]
        self.assertEqual(checked_url, self.tracker.login_url)

    @patch('monitorrent.plugins.trackers.rutracker.update_headers_and_cookies_mixin')
    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_uses_solved_cloudflare_credentials(self, post, mixin):
        # whatever the challenge solver produced has to reach the login request
        solved_headers = {'User-Agent': 'solved-agent'}
        solved_cookies = {'cf_clearance': 'solved-clearance'}
        mixin.return_value = (solved_headers, solved_cookies)
        login_result = Mock()
        login_result.url = 'https://rutracker.org/forum/index.php'
        post.return_value = login_result

        try:
            self.tracker.login(helper.fake_login, helper.fake_password)
        except RutrackerLoginFailedException:
            pass

        self.assertEqual(post.call_args[1]['headers'], solved_headers)
        self.assertEqual(post.call_args[1]['cookies'], solved_cookies)

    def test_get_id(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_id(url), "5062041")

    def test_get_download_url(self):
        for url in self.urls_to_check:
            self.assertEqual(self.tracker.get_download_url(url), "https://rutracker.org/forum/dl.php?t=5062041")

    def test_get_download_url_error(self):
        self.assertIsNone(self.tracker.get_download_url("http://not.rutracker.org/forum/viewtopic.php?t=5062041"))

    @patch('monitorrent.plugins.trackers.rutracker.update_headers_and_cookies_mixin')
    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_reports_block_apart_from_bad_credentials(self, post, mixin):
        # a Cloudflare block must not be reported as wrong credentials
        mixin.return_value = ({}, {})
        blocked = Mock()
        blocked.url = self.tracker.login_url
        blocked.status_code = 403
        post.return_value = blocked

        with self.assertRaises(RutrackerLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)

        self.assertNotEqual(e.exception.code, 1)
        self.assertIn('Cloudflare', e.exception.message)
