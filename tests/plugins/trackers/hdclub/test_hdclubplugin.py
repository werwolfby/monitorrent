# coding=utf-8
import six
import pytest
from mock import Mock, patch

from monitorrent.plugins.trackers import CloudflareChallengeSolverSettings
from monitorrent.plugins.trackers.hdclub import HdclubPlugin, HdclubTopic
from tests import use_vcr, DbTestCase
from tests.plugins.trackers import TrackerSettingsMock


class TestHdclubPlugin(DbTestCase):
    def setUp(self):
        super(TestHdclubPlugin, self).setUp()

        cloudflare_challenge_solver_settings = CloudflareChallengeSolverSettings(False, 10000, False, False, 0)
        self.tracker_settings = TrackerSettingsMock(10, None, cloudflare_challenge_solver_settings)
        self.plugin = HdclubPlugin()
        self.plugin.init(self.tracker_settings)

    def test_can_parse_url_success(self):
        urls = [
            'http://hdclub.org/details.php?id=20000',
            'https://hdclub.org/details.php?id=20000',
        ]

        for url in urls:
            assert self.plugin.can_parse_url(url)

    def test_cannot_parse_url_success(self):
        urls = [
            'http://hdclub.com/details.php?id=20000',
            'https://not.hdclub.org/details.php?id=20000',
        ]

        for url in urls:
            assert not self.plugin.can_parse_url(url)

    @use_vcr
    def test_parse_url_success(self):
        urls = [
            'http://hdclub.org/details.php?id=20000',
            'https://hdclub.org/details.php?id=20000',
        ]

        display_name = u'Донни Браско / Donnie Brasco (1997) [Extended Cut] 1080p BD-Remux'
        for url in urls:
            assert self.plugin.parse_url(url) == {'original_name': display_name}

    def test_execute_success(self):
        topics = [HdclubTopic()]
        engine = Mock()
        self.plugin.update_credentials({'passkey': '12345678'})

        with patch("monitorrent.plugins.trackers.ExecuteWithHashChangeMixin.execute") as execute_mock:
            self.plugin.execute(topics, engine)

            execute_mock.assert_called_once_with(topics, engine)

    def test_execute_failed(self):
        topics = [HdclubTopic()]
        engine = Mock()

        with patch("monitorrent.plugins.trackers.ExecuteWithHashChangeMixin.execute") as execute_mock:
            self.plugin.execute(topics, engine)

            execute_mock.assert_not_called()

    def test_execute_failed_2(self):
        topics = [HdclubTopic()]
        engine = Mock()
        self.plugin.update_credentials({'passkey': ''})

        with patch("monitorrent.plugins.trackers.ExecuteWithHashChangeMixin.execute") as execute_mock:
            self.plugin.execute(topics, engine)

            execute_mock.assert_not_called()

    def test_prepare_request_success(self):
        topic = HdclubTopic()
        with patch("monitorrent.plugins.trackers.hdclub.HdclubTracker.get_download_url") as get_download_url_mock:
            get_download_url_mock.return_value = 'http://hdclub.org/download.php?id=1'
            download_url = self.plugin._prepare_request(topic)

            assert download_url == 'http://hdclub.org/download.php?id=1'
