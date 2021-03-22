from datetime import datetime

import pytest
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
from tests import DbTestCase, ReadContentMixin, use_vcr
from mock import patch, Mock

def new(name, data):
    return type(name, (object,), data)

@ddt
class QBittorrentPluginTest(ReadContentMixin, DbTestCase):
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

        self.assertFalse(plugin.check_connection())

        qbittorrent_client.assert_called_with(host=QBittorrentClientPlugin.ADDRESS_FORMAT.format('localhost', QBittorrentClientPlugin.DEFAULT_PORT),
                                               username='monitorrent', password='monitorrent')

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent(self, qbittorrent_client):
        client = qbittorrent_client.return_value

        torrent_hash = "D27C8E30F0C12AFE84735B57F6463266B118ACEA"
        date_added = datetime(2015, 10, 9, 12, 3, 55, tzinfo=pytz.reference.LocalTimezone())

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent_info = new('torrent', {'name': 'Torrent 1', 'info': new('info', {'added_on': date_added.astimezone(pytz.utc).timestamp()})})
        client.torrents_info.return_value = [torrent_info]

        torrent = plugin.find_torrent(torrent_hash)

        self.assertEqual({'name': 'Torrent 1', 'date_added': date_added.astimezone(pytz.utc)}, torrent)

        client.torrents_info.assert_called_once_with(hashes=[torrent_hash.lower()])

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent_failed(self, qbittorrent_client):
        client = qbittorrent_client.return_value
        client.torrents_info.return_value = []

        plugin = QBittorrentClientPlugin()
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)
        self.assertFalse(plugin.find_torrent(torrent_hash))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_find_torrent_no_settings(self, qbittorrent_client):
        client = qbittorrent_client.return_value
        
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        plugin = QBittorrentClientPlugin()

        plugin.find_torrent(torrent_hash)

        client.torrents_info.assert_not_called()

    def test_add_torrent_bad_settings(self):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_add_torrent_success(self, qbittorrent_client):
        torrent = self.read_httpretty_content('Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent', 'rb')
        client = qbittorrent_client.return_value
        client.torrents_add.return_value = 'Ok.'
        torrent_info = [
            new('torrent', {
                'name': 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4',
                'info': new('info', {
                    "added_on": 1616424630
                })
            })
        ]
        client.torrents_info.return_value = torrent_info

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        self.assertEqual(True, plugin.add_torrent(torrent, None))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_add_torrent_with_settings_success(self, qbittorrent_client):
        torrent = self.read_httpretty_content('Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent', 'rb')
        client = qbittorrent_client.return_value
        client.torrents_add.return_value = 'Ok.'
        torrent_info = [
            new('torrent', {
                'name': 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4',
                'info': new('info', {
                    "added_on": 1616424630
                })
            })
        ]
        client.torrents_info.return_value = torrent_info

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        self.assertEqual(True, plugin.add_torrent(torrent, TopicSettings("/path/to/download")))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_remove_torrent_bad_settings(self, qbittorrent_client):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.remove_torrent(torrent))

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_remove_torrent_success(self, qbittorrent_client):
        client = qbittorrent_client.return_value
        client.torrents_delete.return_value = 'Ok.'

        plugin = QBittorrentClientPlugin()
        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.remove_torrent(torrent))

        client.torrents_delete.assert_called_once_with(hashes=[torrent.lower()])

    @patch('monitorrent.plugins.clients.qbittorrent.Client')
    def test_get_download_dir_success(self, qbittorrent_client):
        client = qbittorrent_client.return_value
        client.app_default_save_path.return_value = '/mnt/media/downloads'

        plugin = QBittorrentClientPlugin()

        assert plugin.get_download_dir() is None

        settings = self.DEFAULT_SETTINGS
        plugin.set_settings(settings)

        assert plugin.get_download_dir() == u'/mnt/media/downloads'

        client.app_default_save_path.assert_called_once()

    def test_decorate_post_method(self):
        client = QBittorrentPluginTest.ClassWithPostMethod()
        client = QBittorrentClientPlugin._decorate_post(client)

        (args, kwargs) = client._post(torrent_contents=[('file.torrent', b'torrent')])

        assert len(args) == 0
        assert len(kwargs) == 1
        assert 'files' in kwargs
        assert kwargs['files'] == [('file.torrent', b'torrent')]

    class ClassWithPostMethod(object):
        def _post(self, *args, **kwargs):
            return (args, kwargs)
