import base64
from collections import namedtuple
from datetime import datetime
from mock import patch
from ddt import ddt, data
import transmissionrpc
from monitorrent.tests import DbTestCase
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

        self.assertFalse(plugin.check_connection())

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
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.get_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_find_torrent_get_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        rpc_client.get_torrent.side_effect = KeyError
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.get_torrent.assert_called_once_with(torrent_hash.lower(),
                                                       ['id', 'hashString', 'addedDate', 'name'])

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent))

        rpc_client.add_torrent.assert_called_once_with(base64.encodebytes(torrent))

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent_without_credentials(self, transmission_client):
        rpc_client = transmission_client.return_value

        plugin = TransmissionClientPlugin()

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent))

        rpc_client.add_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_add_torrent_add_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.add_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent))

        rpc_client.add_torrent.assert_called_once_with(base64.encodebytes(torrent))

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
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.remove_torrent.assert_not_called()

    @patch('monitorrent.plugins.clients.transmission.transmissionrpc.Client')
    def test_remove_torrent_remove_torrent_exception(self, transmission_client):
        rpc_client = transmission_client.return_value
        rpc_client.remove_torrent.side_effect = transmissionrpc.TransmissionError

        plugin = TransmissionClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.remove_torrent.assert_called_once_with(torrent_hash.lower(), delete_data=False)
