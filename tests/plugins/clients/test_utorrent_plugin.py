from ddt import ddt
from mock import patch, Mock, MagicMock
from requests import Response

from monitorrent.plugins.clients.utorrent import UTorrentClientPlugin
from tests import DbTestCase, use_vcr


@ddt
class UTorrentPluginTest(DbTestCase):
    real_host = "http://localhost"
    real_port = 8080
    real_login = "admin"
    real_password = "password"

    bad_host = "http://fake.com"
    bad_port = 1234
    bad_login = "fake"
    bad_password = "more_fake"

    def test_settings(self):
        plugin = UTorrentClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()
        self.assertEqual({'host': 'localhost', 'port': None, 'username': 'monitorrent'}, readed_settings)

    @use_vcr
    def test_check_connection_successfull(self):
        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        self.assertTrue(plugin.check_connection())

    def test_check_connection_failed(self):
        import monitorrent.plugins.clients.utorrent

        with patch.object(monitorrent.plugins.clients.utorrent.requests.Session, 'get', side_effect=Exception):
            plugin = UTorrentClientPlugin()
            settings = {'host': self.bad_host, 'port': self.bad_port, 'username': self.bad_login,
                        'password': self.bad_password}
            plugin.set_settings(settings)
            self.assertFalse(plugin.check_connection())

    @use_vcr
    def test_find_torrent(self):
        plugin = UTorrentClientPlugin()
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        settings = {'host': self.real_host, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        torrent = plugin.find_torrent(torrent_hash)
        self.assertIsNone(torrent['date_added'])
        self.assertIsNotNone(torrent['name'])

    def test_find_torrent_no_settings(self):
        import monitorrent.plugins.clients.utorrent

        with patch.object(monitorrent.plugins.clients.utorrent.requests.Session, 'get', side_effect=Exception):
            plugin = UTorrentClientPlugin()
            torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
            settings = {'host': self.bad_host, 'port': self.bad_port, 'username': self.bad_login,
                        'password': self.bad_password}
            plugin.set_settings(settings)
            torrent = plugin.find_torrent(torrent_hash)
            self.assertFalse(torrent)

    @patch('requests.Session.get')
    def test_find_torrent_failed(self, get_mock):
        response = Response()
        response._content = b"<html><div id=''token'' style=''display:none;''>FKWBGjUDYXGNX7I-UBo5-UiWK1MUOaDmjjrorxOTzmEq3b0lWpr4no8v-FYAAAAA</div></html>"
        get_mock.return_value = response
        plugin = UTorrentClientPlugin()
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        torrent = plugin.find_torrent(torrent_hash)
        self.assertFalse(torrent)

    @patch('requests.Session.get')
    def test_add_torrent_bad_settings(self, get_mock):
        plugin = UTorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_add_torrent_failed(self, post_mock, get_mock):
        response = Response()
        response._content = b"<html><div id=''token'' style=''display:none;''>FKWBGjUDYXGNX7I-UBo5-UiWK1MUOaDmjjrorxOTzmEq3b0lWpr4no8v-FYAAAAA</div></html>"
        response.status_code = 200

        get_mock.return_value = response
        post_mock.side_effect = Exception('boom')

        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_add_torrent_success(self, post_mock, get_mock):
        response = Response()
        response._content = b"<html><div id=''token'' style=''display:none;''>FKWBGjUDYXGNX7I-UBo5-UiWK1MUOaDmjjrorxOTzmEq3b0lWpr4no8v-FYAAAAA</div></html>"
        response.status_code = 200
        good_response = Response()
        good_response.status_code = 200
        get_mock.return_value = response
        post_mock.return_value = good_response

        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.add_torrent(torrent, None))

    @patch('requests.Session.get')
    def test_remove_torrent_bad_settings(self, get_mock):
        plugin = UTorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.remove_torrent(torrent))

    @patch('requests.Session.get')
    def test_remove_torrent_failed(self, get_mock):
        response = Response()
        response._content = b"<html><div id=''token'' style=''display:none;''>FKWBGjUDYXGNX7I-UBo5-UiWK1MUOaDmjjrorxOTzmEq3b0lWpr4no8v-FYAAAAA</div></html>"
        response.status_code = 200

        get_mock.side_effect = [response, Exception('boom')]

        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertFalse(plugin.remove_torrent(torrent))

    @patch('requests.Session.get')
    def test_remove_torrent_success(self, get_mock):
        response = Response()
        response._content = b"<html><div id=''token'' style=''display:none;''>FKWBGjUDYXGNX7I-UBo5-UiWK1MUOaDmjjrorxOTzmEq3b0lWpr4no8v-FYAAAAA</div></html>"
        response.status_code = 200
        good_response = Response()
        good_response.status_code = 200
        get_mock.side_effect = [response, good_response]

        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.remove_torrent(torrent))

    @use_vcr
    def test_get_download_status_success(self):
        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = "44E416FCD3DBF967E292B1C1965306EA86FDB74D"
        result = plugin.get_download_status(torrent)

        assert result.upload_speed == 11
        assert result.download_speed == 10
        assert result.downloaded_bytes == 3821779548
        assert result.total_bytes == 3821779548

    @patch('requests.Session.get')
    def test_get_download_status_bad_settings(self, get_mock):
        plugin = UTorrentClientPlugin()
        torrent = 'torrent'
        self.assertFalse(plugin.get_download_status(torrent))

    @use_vcr
    def test_get_download_status_not_found(self):
        plugin = UTorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = "torrent"
        assert plugin.get_download_status(torrent) is False
