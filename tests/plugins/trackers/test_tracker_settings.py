import pytest
from playwright.sync_api import ProxySettings
from monitorrent.plugins.trackers import TrackerSettings


class TestTrackerSettings(object):
    def test_get_requests_kwargs(self):
        tracker_settings = TrackerSettings(10, 30000, None)
        kwargs = tracker_settings.get_requests_kwargs()

        assert len(kwargs) == 2
        assert 'timeout' in kwargs
        assert 'proxies' in kwargs
        assert kwargs['timeout'] == 10
        assert kwargs['proxies'] is None

    @pytest.mark.parametrize(["proxies", "server", "username", "password"], [
        ({'http': "https://admin:12345@www.proxy.com"}, "https://www.proxy.com", 'admin', '12345'),
        ({'https': "https://www.proxy.com"}, "https://www.proxy.com", None, None),
        ({'http': "http://www.proxy.com"}, "http://www.proxy.com", None, None),
        ({'http': "https://www.proxy.com", 'https': "https://www.proxy.com"}, "https://www.proxy.com", None, None),
        ({'http': "https://admin:12345@www.proxy.com", 'https': "https://admin:12345@www.proxy.com"},
         "https://www.proxy.com", 'admin', '12345'),
    ])
    def test_get_extract_cloudflare_kwargs(self, proxies, server, username, password):
        tracker_settings = TrackerSettings(10, 30000, proxies)
        kwargs = tracker_settings.get_extract_cloudflare_kwargs()

        assert len(kwargs) == 3
        assert 'playwright_timeout' in kwargs
        assert 'proxies' in kwargs
        assert 'proxy' in kwargs
        assert kwargs['playwright_timeout'] == 30000
        assert kwargs['proxies'] == proxies

        proxy: ProxySettings = kwargs['proxy']

        assert proxy['server'] == server
        assert proxy['username'] == username
        assert proxy['password'] == password
