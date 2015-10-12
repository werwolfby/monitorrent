from threading import Event, Lock
from ddt import ddt, data
from time import time, sleep
from datetime import datetime
from mock import Mock, MagicMock, PropertyMock, patch
from monitorrent.utils.bittorrent import Torrent
from monitorrent.tests import TestCase, DbTestCase
from monitorrent.engine import Engine, Logger, EngineRunner, DBEngineRunner, ExecuteSettings
from monitorrent.plugin_managers import ClientsManager, TrackersManager


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


@ddt
class EngineRunnerTest(TestCase):
    class Bunch(object):
        pass

    def test_stop_bofore_execute(self):
        trackers_manager = TrackersManager({})
        execute_mock = MagicMock()
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=0.1)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        execute_mock.assert_not_called()

    def test_stop_after_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        trackers_manager = TrackersManager({})
        execute_mock = Mock(side_effect=execute)
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=0.1)
        waiter.wait(1)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(1, execute_mock.call_count)

    @data(2, 5, 10)
    def test_stop_after_multiple_execute(self, value):
        waiter = Event()
        scope = self.Bunch()
        scope.execute_count = 0

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            scope.execute_count += 1
            if scope.execute_count < value:
                return
            waiter.set()

        trackers_manager = TrackersManager({})
        execute_mock = Mock(side_effect=execute)
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=0.1)
        waiter.wait(2)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(value, execute_mock.call_count)

    @data(0.1, 0.3, 0.5, 0.6)
    def test_update_interval_during_execute(self, test_interval):
        waiter = Event()
        scope = self.Bunch()
        scope.first_execute = True

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            engine_runner.interval = test_interval
            if scope.first_execute:
                scope.start = time()
                scope.first_execute = False
            else:
                scope.end = time()
                waiter.set()

        trackers_manager = TrackersManager({})
        execute_mock = Mock(side_effect=execute)
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=0.1)
        waiter.wait(2)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(2, execute_mock.call_count)

        # noinspection PyUnresolvedReferences
        delta = scope.end - scope.start

        self.assertLessEqual(abs(delta - test_interval), 0.01)

    def test_manual_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        trackers_manager = TrackersManager({})
        execute_mock = Mock(side_effect=execute)
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=1)
        engine_runner.execute()
        waiter.wait(0.3)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(1, execute_mock.call_count)

    def test_exeption_in_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()
            raise Exception('Some error')

        trackers_manager = TrackersManager({})
        execute_mock = Mock(side_effect=execute)
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), trackers_manager, clients_manager, interval=0.1)
        waiter.wait(1)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(1, execute_mock.call_count)


@ddt
class DBExecuteEngineTest(DbTestCase):
    @data(10, 200, 3600, 7200)
    def test_set_interval(self, value):
        trackers_manager = TrackersManager({})
        execute_mock = Mock()
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = DBEngineRunner(Logger(), trackers_manager, clients_manager)

        self.assertEqual(7200, engine_runner.interval)

        engine_runner.interval = value

        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())
        engine_runner = DBEngineRunner(Logger(), trackers_manager, clients_manager)

        self.assertEqual(value, engine_runner.interval)

        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

    class TestDatetime(datetime):
        mock_now = None

        @classmethod
        def now(cls, tz=None):
            return cls.mock_now

    def test_get_last_execute(self):
        trackers_manager = TrackersManager({})
        execute_mock = Mock()
        trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})

        self.TestDatetime.mock_now = datetime.now()

        with patch('monitorrent.engine.datetime', self.TestDatetime(2015, 8, 28)):
            engine_runner = DBEngineRunner(Logger(), trackers_manager, clients_manager)

            self.assertIsNone(engine_runner.last_execute)

            engine_runner.execute()
            sleep(0.1)

            engine_runner.stop()
            engine_runner.join(1)
            self.assertFalse(engine_runner.is_alive())
            engine_runner = DBEngineRunner(Logger(), trackers_manager, clients_manager)

            self.assertEqual(self.TestDatetime.mock_now, engine_runner.last_execute)

            engine_runner.stop()
            engine_runner.join(1)
            self.assertFalse(engine_runner.is_alive())
