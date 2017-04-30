import base64
from collections import namedtuple
from datetime import datetime

import pytest
from mock import patch, Mock
from ddt import ddt
import transmissionrpc

from tests import DbTestCase
from monitorrent.plugins.clients import TopicSettings
from monitorrent.plugins.clients.transmission import TransmissionClientPlugin
import pytz
import pytz.reference


@ddt
class TransmissionPluginTest(DbTestCase):
    def test_settings(self):
        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        expected = {'host': 'localhost', 'port': TransmissionClientPlugin.DEFAULT_PORT, 'username': 'monitorrent'}
        self.assertEqual(expected, readed_settings)

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_check_connection_successfull(self, transmission_client):
        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        self.assertNotEqual(False, plugin.check_connection())

        transmission_client.assert_called_with(address='localhost', port=TransmissionClientPlugin.DEFAULT_PORT,
                                               user='monitorrent', password='monitorrent')

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_check_connection_without_credentials(self, transmission_client):
        plugin = TransmissionClientPlugin()

        self.assertFalse(plugin.check_connection())

        transmission_client.assert_not_called()

        transmission_client.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_check_connection_connect_exception(self, transmission_client):
        transmission_client.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.check_connection()

        transmission_client.assert_called_with(address='localhost', port=TransmissionClientPlugin.DEFAULT_PORT,
                                               user='monitorrent', password='monitorrent')

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_find_torrent(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        date_added = datetime(2015, 10, 9, 12, 3, 55, tzinfo=pytz.reference.LocalTimezone())
        torrent_hash = 'SomeRandomHashMockString'

        torrent_class = namedtuple('Torrent', ['name', 'date_added'])

        rpc_client.get_torrent.return_value = torrent_class(name='Torrent 1', date_added=date_added)

        torrent = plugin.find_torrent(torrent_hash)

        self.assertEqual({'name': 'Torrent 1', 'date_added': date_added.astimezone(pytz.utc)}, torrent)

        rpc_client.get_torrent.assert_called_once_with(torrent_hash.lower(),
                                                       ['id', 'hashString', 'addedDate', 'name'])

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_find_torrent_without_credentials(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()

        torrent_hash = 'SomeRandomHashMockString'
        assert plugin.find_torrent(torrent_hash) is False

        rpc_client.get_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_find_torrent_get_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        rpc_client.get_torrent.side_effect = KeyError
        with pytest.raises(KeyError) as e:
            plugin.find_torrent(torrent_hash)

        rpc_client.get_torrent.assert_called_once_with(torrent_hash.lower(),
                                                       ['id', 'hashString', 'addedDate', 'name'])

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent, None))

        rpc_client.add_torrent.assert_called_once_with(base64.b64encode(torrent).decode('utf-8'))

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent_with_settings(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent, TopicSettings('/path/to/download/dir')))

        rpc_client.add_torrent.assert_called_once_with(base64.b64encode(torrent).decode('utf-8'),
                                                       download_dir='/path/to/download/dir')

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent_without_credentials(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent, None))

        rpc_client.add_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent_add_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.add_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.add_torrent(torrent, None)

        rpc_client.add_torrent.assert_called_once_with(base64.b64encode(torrent).decode('utf-8'))

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_remove_torrent(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertTrue(plugin.remove_torrent(torrent_hash))

        rpc_client.remove_torrent.assert_called_once_with(torrent_hash.lower(), delete_data=False)

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_remove_torrent_without_credentials(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()

        torrent_hash = 'SomeRandomHashMockString'
        assert plugin.remove_torrent(torrent_hash) is False

        rpc_client.remove_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_remove_torrent_remove_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.remove_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.remove_torrent(torrent_hash)

        rpc_client.remove_torrent.assert_called_once_with(torrent_hash.lower(), delete_data=False)

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_get_download_dir_success(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_session.return_value = transmissionrpc.Session(fields={'download_dir': '/mnt/media/downloads'})

        plugin = TransmissionClientPlugin()

        assert plugin.get_download_dir() is None

        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        assert plugin.get_download_dir() == u'/mnt/media/downloads'

        rpc_client.get_session.assert_called_once()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_get_download_dir_exception(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_session.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.get_download_dir()

        rpc_client.get_session.assert_called_once()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_get_status_by_hash(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_torrent.return_value = namedtuple('Torrent',
                                                         ('rateDownload', 'totalSize', 'downloadedEver',
                                                          'rateUpload', 'status', 'progress', 'ratio')
                                                         )(5000, 10000, 6000, 20, 'downloading', 23, 1)

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        status = plugin.get_download_status_by_hash('4e2597302ad6b4d7a545c8ec02621ac232316b96')
        assert status.downloaded_bytes == 6000
        assert status.download_speed == 5000
        assert status.total_bytes == 10000
        assert status.upload_speed == 20

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_fail_when_no_settings_for_get_status_by_hash(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        assert plugin.get_download_status_by_hash('4e2597302ad6b4d7a545c8ec02621ac232316b96') == False
        rpc_client.get_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_fail_get_status_by_hash_when_get_torrent_fails(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.get_download_status_by_hash('4e2597302ad6b4d7a545c8ec02621ac232316b96')

        rpc_client.get_torrent.assert_called_once()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_get_status(self, transmission_client):
        rpc_client = transmission_client.return_value
        torrent_id = '4e2597302ad6b4d7a545c8ec02621ac232316b96'
        rpc_client.get_torrents.return_value = [namedtuple('Torrent',
                                                           ('hashString', 'rateDownload', 'totalSize', 'downloadedEver',
                                                            'rateUpload', 'status', 'progress', 'ratio')
                                                           )(torrent_id, 5000, 10000, 6000, 20, 'downloading', 23, 1)]

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        statuses = plugin.get_download_status()
        assert torrent_id in statuses
        status = statuses[torrent_id]
        assert status.downloaded_bytes == 6000
        assert status.download_speed == 5000
        assert status.total_bytes == 10000
        assert status.upload_speed == 20

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_fail_when_no_settings_for_get_status(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_torrents.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()

        assert plugin.get_download_status() is False
        rpc_client.get_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_should_fail_get_status_when_get_torrent_fails(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.get_torrents.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        with pytest.raises(transmissionrpc.TransmissionError) as e:
            plugin.get_download_status()

        rpc_client.get_torrents.assert_called_once()
