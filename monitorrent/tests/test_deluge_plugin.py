from mock import patch
from ddt import ddt, data
from monitorrent.tests import DbTestCase
from monitorrent.plugins.clients.deluge import DelugeClientPlugin


def ssl_wrap_socket(socket):
    return socket


@ddt
class DelugePluginTest(DbTestCase):
    def test_settings(self):
        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        self.assertEqual({'host': 'localhost', 'port': None, 'username': 'monitorrent'}, readed_settings)

    @data(True, False)
    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_successfull(self, value, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = value

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        self.assertEqual(value, plugin.check_connection())

        deluge_client.assert_called_with('localhost', DelugeClientPlugin.DEFAULT_PORT, 'monitorrent', 'monitorrent')

        connect_mock = rpc_client.connect
        connect_mock.assert_called_once_with()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_failed(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        self.assertFalse(plugin.check_connection())

        deluge_client.assert_not_called()

        connect_mock = rpc_client.connect
        connect_mock.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_connect_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connect.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        self.assertFalse(plugin.check_connection())

        deluge_client.assert_called_with('localhost', DelugeClientPlugin.DEFAULT_PORT, 'monitorrent', 'monitorrent')

        connect_mock = rpc_client.connect
        connect_mock.assert_called_once_with()
