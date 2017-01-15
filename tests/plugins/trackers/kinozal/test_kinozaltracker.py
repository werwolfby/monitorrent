# coding=utf-8
from mock import patch, Mock
from pytest import raises
from monitorrent.plugins.trackers.kinozal import KinozalTracker, KinozalLoginFailedException
from tests import use_vcr
from tests.plugins.trackers import TrackerSettingsMock
from tests.plugins.trackers.kinozal.kinozal_helper import KinozalHelper


helper = KinozalHelper()
# helper = KinozalHelper.login('realusername', 'realpassword')


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
