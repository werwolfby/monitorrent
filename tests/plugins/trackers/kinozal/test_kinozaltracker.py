# coding=utf-8
import pytz
import pytest
from datetime import datetime
from mock import patch, Mock
from pytest import raises
from monitorrent.plugins.trackers.kinozal import KinozalDateParser, KinozalTracker, KinozalLoginFailedException
from tests import use_vcr
from tests.plugins.trackers import TrackerSettingsMock
from tests.plugins.trackers.kinozal.kinozal_helper import KinozalHelper


helper = KinozalHelper()
# helper = KinozalHelper.login('realusername', 'realpassword')


class MockDatetime(datetime):
    mock_now = None

    @classmethod
    def now(cls, tz=None):
        return cls.mock_now


class TestKinozalTracker(object):
    def setup(self):
        self.tracker_settings = TrackerSettingsMock(10, None)
        self.tracker = KinozalTracker()
        self.tracker.tracker_settings = self.tracker_settings
        self.urls_to_check = [
            "http://kinozal.tv/details.php?id=1506818"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            assert self.tracker.can_parse_url(url)

        bad_urls = [
            "http://kinozal.com/details.php?id=1506818",
        ]
        for url in bad_urls:
            assert not self.tracker.can_parse_url(url)

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.tracker.parse_url("http://kinozal.tv/details.php?id=1506818")
        assert parsed_url['original_name'] == u'Война против всех / War on Everyone / 2016 / ДБ / WEB-DLRip'

    @use_vcr
    def test_parse_wrong_url(self):
        assert not self.tracker.parse_url('http://kinozal.com/details.php?id=1506818')
        # special case for not existing topic
        assert not self.tracker.parse_url('http://kinozal.tv/details.php?id=1906818')

    @use_vcr
    def test_login_failed(self):
        with raises(KinozalLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        assert e.value.code == 1
        assert e.value.message == 'Invalid login or password'

    @helper.use_vcr(inject_cassette=True)
    def test_login(self, cassette):
        c_pass = helper.fake_pass if len(cassette.data) > 0 else helper.real_pass
        c_uid = helper.fake_uid if len(cassette.data) > 0 else helper.real_uid

        self.tracker.login(helper.real_login, helper.real_password)

        assert self.tracker.c_pass == c_pass
        assert self.tracker.c_uid == c_uid

    @patch('monitorrent.plugins.trackers.rutracker.Session.post')
    def test_login_failed_cookie(self, post):
        login_result = Mock()
        login_result.url = 'http://kinozal.tv/userdetails.php?id=10000000'
        post.return_value = login_result
        with raises(KinozalLoginFailedException) as e:
            self.tracker.login(helper.fake_login, helper.fake_password)
        assert e.value.code == 2
        assert e.value.message == 'Failed to retrieve cookie'

    @helper.use_vcr
    def test_verify(self):
        self.tracker.setup(helper.real_uid, helper.real_pass)
        assert self.tracker.verify()

    @use_vcr
    def test_verify_failed(self):
        self.tracker.setup(None, None)
        assert not self.tracker.verify()

        self.tracker.setup('12345', None)
        assert not self.tracker.verify()

        self.tracker.setup(None, 'AsDfGhJkL')
        assert not self.tracker.verify()

        self.tracker.setup('12345', 'AsDfGhJkL')
        assert not self.tracker.verify()

    def test_get_id(self):
        for url in self.urls_to_check:
            assert self.tracker.get_id(url) == "1506818"

    def test_get_download_url(self):
        for url in self.urls_to_check:
            assert self.tracker.get_download_url(url) == "http://dl.kinozal.tv/download.php?id=1506818"

    def test_get_download_url_error(self):
        assert not self.tracker.get_download_url("http://not.kinozal.com/details.php?id=1506818")

    @use_vcr
    def test_get_last_torrent_update_for_updated_yesterday_success(self):
        url = 'http://kinozal.tv/details.php?id=1831370'
        expected = KinozalDateParser.tz_moscow.localize(datetime(2021, 3, 18, 23, 12)).astimezone(pytz.utc)

        server_now = datetime(2021, 3, 19, 12, 0, 0, tzinfo=pytz.utc)
        MockDatetime.mock_now = server_now

        with patch('monitorrent.plugins.trackers.kinozal.datetime.datetime', MockDatetime):
            assert self.tracker.get_last_torrent_update(url) == expected

    @use_vcr
    def test_get_last_torrent_update_for_updated_today_success(self):
        url = 'http://kinozal.tv/details.php?id=1496310'
        expected = KinozalDateParser.tz_moscow.localize(datetime(2017, 1, 20, 1, 30)).astimezone(pytz.utc)

        server_now = datetime(2017, 1, 20, 12, 0, 0, tzinfo=pytz.utc)
        MockDatetime.mock_now = server_now

        with patch('monitorrent.plugins.trackers.kinozal.datetime.datetime', MockDatetime):
            assert self.tracker.get_last_torrent_update(url) == expected

    @use_vcr
    def test_get_last_torrent_update_for_updated_in_particular_success(self):
        url = 'http://kinozal.tv/details.php?id=1508210'
        expected = KinozalDateParser.tz_moscow.localize(datetime(2017, 1, 26, 21, 24)).astimezone(pytz.utc)

        assert self.tracker.get_last_torrent_update(url) == expected

    @use_vcr
    def test_get_last_torrent_update_without_updates_success(self):
        url = 'http://kinozal.tv/details.php?id=1831382'
        expected = KinozalDateParser.tz_moscow.localize(datetime(2021, 3, 15, 23, 27)).astimezone(pytz.utc)

        assert self.tracker.get_last_torrent_update(url) == expected
