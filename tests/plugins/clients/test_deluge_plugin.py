import base64
import time
from datetime import datetime
from mock import patch
from ddt import ddt, data
import pytz
import pytz.reference
from tests import DbTestCase
from monitorrent.plugins.clients import TopicSettings
from monitorrent.plugins.clients.deluge import DelugeClientPlugin


@ddt
class DelugePluginTest(DbTestCase):
    def test_settings(self):
        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        self.assertIsNone(plugin.get_settings())
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

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        date_added = datetime(2015, 10, 9, 12, 3, 55, tzinfo=pytz.reference.LocalTimezone())
        rpc_client.call.return_value = {b'name': b'Torrent 1', b'time_added': time.mktime(date_added.timetuple())}

        torrent_hash = 'SomeRandomHashMockString'
        torrent = plugin.find_torrent(torrent_hash)

        self.assertEqual({'name': 'Torrent 1', 'date_added': date_added.astimezone(pytz.utc)}, torrent)

        rpc_client.call.assert_called_once_with('core.get_torrent_status', torrent_hash.lower(),
                                                ['time_added', 'name'])

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_connect_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.connect.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_false(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.get_torrent_status', torrent_hash.lower(),
                                                ['time_added', 'name'])

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent, None))

        rpc_client.call.assert_called_once_with('core.add_torrent_file', None, base64.b64encode(torrent), None)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent_with_settings(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent, TopicSettings('/path/to/download')))

        options = {
            'download_location': '/path/to/download'
        }

        rpc_client.call.assert_called_once_with('core.add_torrent_file', None, base64.b64encode(torrent), options)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent, None))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent_call_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent, None))

        rpc_client.call.assert_called_once_with('core.add_torrent_file', None, base64.b64encode(torrent), None)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        rpc_client.call.return_value = True

        torrent_hash = 'SomeRandomHashMockString'
        self.assertTrue(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.remove_torrent', torrent_hash.lower(), False)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        rpc_client.call.return_value = True

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent_call_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.remove_torrent', torrent_hash.lower(), False)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_get_download_dir_success(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.return_value = b'/mnt/media/torrents/complete'

        plugin = DelugeClientPlugin()

        assert plugin.get_download_dir() is None

        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        assert plugin.get_download_dir() == u'/mnt/media/torrents/complete'

        rpc_client.call.assert_called_once_with('core.get_config_value', 'move_completed_path')

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_get_download_dir_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        assert plugin.get_download_dir() is None

        rpc_client.call.assert_called_once_with('core.get_config_value', 'move_completed_path')

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_get_torrent_status_by_hash_successfully(self, deluge_client):
        torrent_hash = 'SomeRandomHashMockString'
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.return_value = {str.encode(torrent_hash.lower()): {b'total_done': 30,
                                                                           b'total_size': 100,
                                                                           b'download_payload_rate': 50000.0,
                                                                           b'upload_payload_rate': 0.0}}

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        result = plugin.get_download_status_by_hash(torrent_hash)
        assert result.download_speed == 50000.0
        assert result.upload_speed == 0.0
        assert result.total_bytes == 100
        assert result.downloaded_bytes == 30

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_fail_when_no_settings_on_get_torrent_status_by_hash(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        torrent_hash = 'SomeRandomHashMockString'

        plugin = DelugeClientPlugin()

        assert plugin.get_download_status_by_hash(torrent_hash) is False

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_fail_get_torrent_status_by_hash_on_error(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        torrent_hash = 'SomeRandomHashMockString'

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        assert plugin.get_download_status_by_hash(torrent_hash) is False

        rpc_client.call.assert_called_once_with("core.get_torrents_status",
                                                {'hash': torrent_hash.lower()},
                                                ['total_done', 'total_size', 'download_payload_rate',
                                                 'upload_payload_rate', 'state', 'progress'])

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_get_torrent_statuses_successfully(self, deluge_client):
        torrent_hash = 'SomeRandomHashMockString'
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.return_value = {str.encode(torrent_hash.lower()): {b'total_done': 30,
                                                                           b'total_size': 100,
                                                                           b'download_payload_rate': 50000.0,
                                                                           b'upload_payload_rate': 0.0}}

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        result = plugin.get_download_status().popitem()[1]
        assert result.download_speed == 50000.0
        assert result.upload_speed == 0.0
        assert result.total_bytes == 100
        assert result.downloaded_bytes == 30

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_fail_when_no_settings_on_get_torrent_statuses(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()

        assert plugin.get_download_status() is False

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_should_fail_get_torrent_status_on_error(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        assert plugin.get_download_status() is False

        rpc_client.call.assert_called_once_with("core.get_torrents_status",
                                                {}, ['total_done', 'total_size', 'download_payload_rate',
                                                     'upload_payload_rate', 'state', 'progress'])
