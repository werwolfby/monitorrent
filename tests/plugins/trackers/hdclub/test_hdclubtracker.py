# coding=utf-8
import six
import pytest
from monitorrent.plugins.trackers.hdclub import HdclubTracker
from tests import use_vcr
from tests.plugins.trackers import TrackerSettingsMock


class TestHdclubTracker(object):
    def setup(self):
        self.tracker_settings = TrackerSettingsMock(10, None)
        self.tracker = HdclubTracker()
        self.tracker.tracker_settings = self.tracker_settings

    def test_can_parse_url_success(self):
        urls = [
            'http://hdclub.org/details.php?id=20000',
            'https://hdclub.org/details.php?id=20000',
        ]

        for url in urls:
            assert self.tracker.can_parse_url(url)

    def test_cannot_parse_url_success(self):
        urls = [
            'http://hdclub.com/details.php?id=20000',
            'https://not.hdclub.org/details.php?id=20000',
        ]

        for url in urls:
            assert not self.tracker.can_parse_url(url)

    @use_vcr
    def test_parse_url_success(self):
        urls = [
            'http://hdclub.org/details.php?id=20000',
            'https://hdclub.org/details.php?id=20000',
        ]

        display_name = u'Донни Браско / Donnie Brasco (1997) [Extended Cut] 1080p BD-Remux'
        for url in urls:
            assert self.tracker.parse_url(url) == {'original_name': display_name}

    @use_vcr
    def test_parse_url_failed(self):
        urls = [
            'http://hdclub.org/details.php?id=1000',
            'https://hdclub.org/details.php?not_id=20000',
        ]

        for url in urls:
            assert not self.tracker.parse_url(url)

    @pytest.mark.parametrize('url,topic_id', [
        ('http://hdclub.org/details.php?id=20000', 20000),
        ('https://hdclub.org/details.php?id=20000', 20000),
        ('https://hdclub.org/details.php?id=12345', 12345),
    ])
    def test_get_id_success(self, url, topic_id):
        assert self.tracker.get_id(url) == topic_id

    @pytest.mark.parametrize('url', [
        'http://hdclub.org/details.php?_id=20000',
        'https://hdclub.org/details.php?notid=20000',
        'https://hdclub.org/details.php?query=12345',
    ])
    def test_get_id_failed(self, url):
        assert self.tracker.get_id(url) is None

    @pytest.mark.parametrize('url,topic_id', [
        ('http://hdclub.org/details.php?id=20000', 20000),
        ('https://hdclub.org/details.php?id=12345', 12345),
        ('http://hdclub.org/details.php?id=54321', 54321)
    ])
    def test_get_download_url_success(self, url, topic_id):
        passkey = '1234567890abcdefghjklmnopqrst'
        self.tracker.setup(passkey)
        download_url = self.tracker.get_download_url(url)
        assert passkey in download_url
        assert six.text_type(topic_id) in download_url

    @pytest.mark.parametrize('url,passkey', [
        ('http://hdclub.org/details.php?not_id=20000', '1234567890abcdefghjklmnopqrst'),
        ('https://hdclub.org/details.php?not_id=20000', '1234567890abcdefghjklmnopqrst'),
        ('https://hdclub.org/details.php?id=12345', None)
    ])
    def test_get_download_url_failed(self, url, passkey):
        self.tracker.setup(passkey)
        assert self.tracker.get_download_url(url) is None
