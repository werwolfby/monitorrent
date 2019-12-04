from datetime import datetime

import pytz
import json
from ddt import ddt
from pytz import reference
from requests import Response
from requests_mock import Mocker
import qbittorrentapi

import monitorrent.plugins.trackers
from monitorrent.plugins.clients import TopicSettings
from monitorrent.plugins.clients.qbittorrent import QBittorrentClientPlugin
from tests import DbTestCase, use_vcr
from mock import patch, Mock

def new(name, data):
    return type(name, (object,), data)

@ddt
class QBittorrentPluginTest(DbTestCase):
    DEFAULT_SETTINGS = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}

    def test_settings(self):
        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        expected = {'host': 'localhost', 'port': None, 'username': 'monitorrent'}
        self.assertEqual(expected, readed_settings)

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_check_connection_successfull(self, qbittorrent_client):
        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        self.assertNotEqual(False, plugin.check_connection())

        qbittorrent_client.assert_called_with(host=QBittorrentClientPlugin.ADDRESS_FORMAT.format('localhost', QBittorrentClientPlugin.DEFAULT_PORT),
                                               username='monitorrent', password='monitorrent')

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_check_connection_failed(self, qbittorrent_client):
        qbittorrent_client.side_effect = qbittorrentapi.APIConnectionError

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        with pytest.raises(qbittorrentapi.APIConnectionError) as e:
            plugin.check_connection()

        qbittorrent_client.assert_called_with(host=QBittorrentClientPlugin.ADDRESS_FORMAT.format('localhost', QBittorrentClientPlugin.DEFAULT_PORT),
                                               username='monitorrent', password='monitorrent')

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value

        torrent_hash = "D27C8E30F0C12AFE84735B57F6463266B118ACEA"
        date_added = datetime(2015, 10, 9, 12, 3, 55, tzinfo=pytz.reference.LocalTimezone())

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent_info = new('torrent', {'name': 'Torrent 1', 'info': new('info', {'added_on': date_added.astimezone(pytz.utc).timestamp()})})
        rpc_client.torrents_info.return_value = [torrent_info]

        torrent = plugin.find_torrent(torrent_hash)

        self.assertEqual({'name': 'Torrent 1', 'date_added': date_added.astimezone(pytz.utc)}, torrent)

        rpc_client.torrents_info.assert_called_once_with(hashes=[torrent_hash.lower()])

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent_failed(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        rpc_client.torrents_info.return_value = []

        plugin = QBittorrentClientPlugin()
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)
        torrent = plugin.find_torrent(torrent_hash)
        self.assertFalse(torrent)

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent_no_settings(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        plugin = QBittorrentClientPlugin()

        torrent = plugin.find_torrent(torrent_hash)

        rpc_client.torrents_info.assert_not_called()

    def test_add_torrent_bad_settings(self):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('requests.Session.post')
    def test_add_torrent_failed(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200

        post_mock.side_effect = [response, Exception('boom')]

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_add_torrent_success(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        rpc_client.torrents_add.return_value = 'Ok.'

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertEqual('Ok.', plugin.add_torrent(torrent, None))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_add_torrent_with_settings_success(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        rpc_client.torrents_add.return_value = 'Ok.'

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertEqual('Ok.', plugin.add_torrent(torrent, TopicSettings("/path/to/download")))

    def test_remove_torrent_bad_settings(self):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.remove_torrent(torrent))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_remove_torrent_failed(self, qbittorrent_client):
        qbittorrent_client.side_effect = qbittorrentapi.HTTP500Error

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        with pytest.raises(qbittorrentapi.HTTP500Error) as e:
            plugin.remove_torrent(torrent)

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_remove_torrent_success(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        rpc_client.torrents_delete.return_value = 'Ok.'

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.remove_torrent(torrent))

        rpc_client.torrents_delete.assert_called_once_with(hashes=[torrent.lower()])

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_get_download_dir_success(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        rpc_client.app_default_save_path.return_value = '/mnt/media/downloads'

        plugin = QBittorrentClientPlugin()

        assert plugin.get_download_dir() is None

        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        assert plugin.get_download_dir() == u'/mnt/media/downloads'

        rpc_client.app_default_save_path.assert_called_once()

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_get_download_dir_error(self, qbittorrent_client):
        rpc_client = qbittorrent_client.return_value
        qbittorrent_client.side_effect = qbittorrentapi.HTTP500Error

        plugin = QBittorrentClientPlugin()

        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        with pytest.raises(qbittorrentapi.HTTP500Error) as e:
            plugin.get_download_dir()
