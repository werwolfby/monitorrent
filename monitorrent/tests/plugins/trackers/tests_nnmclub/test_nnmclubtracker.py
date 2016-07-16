# coding=utf-8
import httpretty
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.nnmclub import NnmClubTracker, LoginResult, NnmClubLoginFailedException
from unittest import TestCase
from monitorrent.tests import use_vcr
from monitorrent.tests.plugins.trackers.tests_nnmclub.nnmclub_helper import NnmClubTrackerHelper

# helper = NnmClubTrackerHelper.login('login@gmail.com', 'p@$$w0rd')
helper = NnmClubTrackerHelper()


class NnmClubTrackerTest(TestCase):
    def setUp(self):
        super(NnmClubTrackerTest, self).setUp()
        self.tracker_settings = TrackerSettings(10)
        self.tracker = NnmClubTracker()
        self.tracker.tracker_settings = self.tracker_settings

    def test_can_parse_url(self):
        self.assertTrue(self.tracker.can_parse_url('http://nnmclub.to/forum/viewtopic.php?t=409969'))
        self.assertTrue(self.tracker.can_parse_url('http://nnm-club.me/forum/viewtopic.php?t=409969'))
        self.assertFalse(self.tracker.can_parse_url('http://not-nnm-club.me/forum/viewtopic.php?t=409969'))

    def test_get_url(self):
        expected = 'http://nnmclub.to/forum/viewtopic.php?t=409969'
        self.assertEqual(self.tracker.get_url('http://nnmclub.to/forum/viewtopic.php?t=409969'), expected)
        self.assertEqual(self.tracker.get_url('http://nnm-club.me/forum/viewtopic.php?t=409969'), expected)

    @use_vcr
    def test_parse_url(self):
        original_name = u'Легенда о Тиле (1976) DVDRip'
        urls = ['http://nnmclub.to/forum/viewtopic.php?t=409969',
                'http://nnm-club.me/forum/viewtopic.php?t=409969']
        for url in urls:
            result = self.tracker.parse_url(url)
            self.assertIsNotNone(result, 'Can\'t parse url={}'.format(url))
            self.assertTrue('original_name' in result, 'Can\'t find original_name for url={}'.format(url))
            self.assertEqual(original_name, result['original_name'])

    @use_vcr()
    def test_parse_url_failed(self):
        urls = ['http://nnmclub.to/forum/viewtopic1.php?t=409969',
                'http://nnm-club.me/forum/login.php',
                'http://not-nnm-club/forum/viewtopic.php?t=409969',
                'http://nnmclub.to/forum/viewtopic.php?t=1']
        for url in urls:
            result = self.tracker.parse_url(url)
            self.assertFalse(result)

    @helper.use_vcr(inject_cassette=True)
    def test_login(self, cassette):
        # login will update cassette
        check_sid = len(cassette) > 0
        self.tracker.login(helper.real_username, helper.real_password)
        if check_sid:
            self.assertTrue((self.tracker.sid == helper.real_sid) or (self.tracker.sid == helper.fake_sid))
        self.assertTrue((self.tracker.user_id == helper.real_user_id) or (self.tracker.user_id == helper.fake_user_id))

    @use_vcr()
    def test_fail_login(self):
        with self.assertRaises(NnmClubLoginFailedException) as cm:
            self.tracker.login("admin@nnmclub.to", "FAKE_PASSWORD")
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(cm.exception.message, u'Invalid login or password')

    @helper.use_vcr(inject_cassette=True)
    def test_verify(self, cassette):
        user_id = helper.fake_user_id if len(cassette) > 0 else helper.real_user_id
        sid = helper.fake_sid if len(cassette) > 0 else helper.real_sid
        tracker = NnmClubTracker(user_id, sid)
        tracker.tracker_settings = self.tracker_settings
        self.assertTrue(tracker.verify())

    def test_verify_false(self):
        self.assertFalse(self.tracker.verify())

    @use_vcr()
    def test_verify_fail(self):
        tracker = NnmClubTracker("9876543", '2' * 32)
        tracker.tracker_settings = self.tracker_settings
        self.assertFalse(tracker.verify())

    @use_vcr()
    def test_get_download_url(self):
        urls = ['http://nnmclub.to/forum/viewtopic.php?t=409969',
                'http://nnm-club.me/forum/viewtopic.php?t=409969']
        for url in urls:
            result = self.tracker.get_download_url(url)
            self.assertEqual(result, 'http://nnmclub.to/forum/download.php?id=370059')

    @helper.use_vcr(inject_cassette=True)
    def test_get_download_url_with_login(self, cassette):
        # login will update cassette
        has_cassette = len(cassette) > 0
        urls = ['http://nnmclub.to/forum/viewtopic.php?t=1035515',
                'http://nnm-club.me/forum/viewtopic.php?t=1035515']
        for url in urls:
            result = self.tracker.get_download_url(url)
            self.assertFalse(result)

        user_id = helper.fake_user_id if has_cassette else helper.real_user_id
        sid = helper.fake_sid if has_cassette else helper.real_sid
        self.tracker.setup(user_id, sid)

        for url in urls:
            result = self.tracker.get_download_url(url)
            self.assertEqual(result, 'http://nnmclub.to/forum/download.php?id=866904')
