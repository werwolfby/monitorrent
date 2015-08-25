from ddt import ddt, data
from datetime import datetime
from mock import Mock, MagicMock
from monitorrent.utils.bittorrent import Torrent
from monitorrent.tests import TestCase
from monitorrent.engine import Engine, Logger
from monitorrent.plugin_managers import ClientsManager


@ddt
class EngineTest(TestCase):
    def setUp(self):
        super(EngineTest, self).setUp()

        self.log_mock = Logger()
        self.log_info_mock = MagicMock()
        self.log_downloaded_mock = MagicMock()
        self.log_failed_mock = MagicMock()

        self.log_mock.info = self.log_info_mock
        self.log_mock.downloaded = self.log_downloaded_mock
        self.log_mock.failed = self.log_failed_mock

        self.clients_manager = ClientsManager()
        self.engine = Engine(self.log_mock, self.clients_manager)

    def test_engine_find_torrent(self):
        finded_torrent = {'date_added': datetime.now()}
        self.clients_manager.find_torrent = MagicMock(return_value=finded_torrent)

        result = self.engine.find_torrent('hash')

        self.assertEqual(finded_torrent, result)

    @data(True, False)
    def test_engine_remove_torrent(self, value):
        self.clients_manager.remove_torrent = MagicMock(return_value=value)

        self.assertEqual(value, self.engine.remove_torrent('hash'))


@ddt
class EngineAddTorrentTest(EngineTest):
    def setUp(self):
        super(EngineAddTorrentTest, self).setUp()

        self.find_torrents_side_effect.__func__.__first_call = True

    class TorrentMock(Torrent):
        # noinspection PyMissingConstructor
        def __init__(self, content, info_hash):
            self.raw_content = content
            self._info_hash = info_hash

        @property
        def info_hash(self):
            return self._info_hash

    HASH1 = 'hash1'
    HASH2 = 'hash2'
    NEW_HASH = 'hash3'
    FIND_TORRENTS1 = {'date_added': datetime(2015, 8, 26, 10, 10, 10), 'name': 'TV Series [s01e01-02]'}
    FIND_TORRENTS2 = {'date_added': datetime(2015, 8, 26, 20, 10, 10), 'name': 'TV Series [s01e01-03]'}
    FIND_TORRENTS3 = {'date_added': datetime(2015, 8, 26, 20, 10, 10), 'name': 'TV Series [s01e01-04]'}

    TORRENT_MOCK = TorrentMock('content', HASH1)

    def find_torrents_side_effect(self, hash_value):
        if hash_value == self.HASH1:
            return self.FIND_TORRENTS1
        if hash_value == self.HASH2:
            return self.FIND_TORRENTS2
        if hash_value == self.NEW_HASH:
            if self.find_torrents_side_effect.__func__.__first_call:
                self.find_torrents_side_effect.__func__.__first_call = False
                return None
            else:
                return self.FIND_TORRENTS3
        return None

    def test_engine_add_torrent_already_added(self):
        self.clients_manager.find_torrent = Mock(side_effect=self.find_torrents_side_effect)
        self.clients_manager.add_torrent = Mock(return_value=True)
        self.clients_manager.remove_torrent = Mock(return_value=True)

        result = self.engine.add_torrent('movie.torrent', self.TORRENT_MOCK, self.HASH2)

        self.assertEqual(result, self.FIND_TORRENTS1['date_added'])

    def test_engine_add_torrent_new_added(self):
        self.clients_manager.find_torrent = Mock(side_effect=self.find_torrents_side_effect)
        self.clients_manager.add_torrent = Mock(return_value=True)
        self.clients_manager.remove_torrent = Mock(return_value=True)

        self.TORRENT_MOCK._info_hash = self.NEW_HASH
        result = self.engine.add_torrent('movie.torrent', self.TORRENT_MOCK, self.HASH2)

        self.assertEqual(result, self.FIND_TORRENTS3['date_added'])

    def test_engine_add_torrent_new_added_not_existing_old(self):
        self.clients_manager.find_torrent = Mock(side_effect=self.find_torrents_side_effect)
        self.clients_manager.add_torrent = Mock(return_value=True)
        self.clients_manager.remove_torrent = Mock(return_value=True)

        self.TORRENT_MOCK._info_hash = self.NEW_HASH
        result = self.engine.add_torrent('movie.torrent', self.TORRENT_MOCK, self.HASH2 + 'random')

        self.assertEqual(result, self.FIND_TORRENTS3['date_added'])

    def test_engine_add_torrent_new_added_cant_remove_old(self):
        self.clients_manager.find_torrent = Mock(side_effect=self.find_torrents_side_effect)
        self.clients_manager.add_torrent = Mock(return_value=True)
        self.clients_manager.remove_torrent = Mock(return_value=False)

        self.TORRENT_MOCK._info_hash = self.NEW_HASH
        result = self.engine.add_torrent('movie.torrent', self.TORRENT_MOCK, self.HASH2)

        self.assertEqual(result, self.FIND_TORRENTS3['date_added'])

    def test_engine_add_torrent_failed(self):
        self.clients_manager.find_torrent = Mock(side_effect=self.find_torrents_side_effect)
        self.clients_manager.add_torrent = Mock(return_value=False)
        self.clients_manager.remove_torrent = Mock(return_value=False)

        self.TORRENT_MOCK._info_hash = self.NEW_HASH
        with self.assertRaises(Exception):
            self.engine.add_torrent('movie.torrent', self.TORRENT_MOCK, self.HASH2)
