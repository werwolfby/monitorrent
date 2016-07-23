from builtins import object
from threading import Event
from ddt import ddt, data
from time import time, sleep
from datetime import datetime, timedelta
from mock import Mock, MagicMock, PropertyMock, patch, call, ANY
import pytz
from monitorrent.utils.bittorrent import Torrent
from monitorrent.tests import TestCase, DbTestCase, DBSession
from monitorrent.engine import Engine, Logger, EngineRunner, DBEngineRunner, DbLoggerWrapper, Execute, ExecuteLog,\
    ExecuteLogManager
from monitorrent.plugin_managers import ClientsManager, TrackersManager
from monitorrent.plugins.trackers import TrackerSettings


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
        finded_torrent = {'date_added': datetime.now(pytz.utc)}
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

    def setUp(self):
        super(EngineRunnerTest, self).setUp()
        self.trackers_manager = TrackersManager(TrackerSettings(10, None), {})

    def test_stop_bofore_execute(self):        
        execute_mock = MagicMock()
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=0.1)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        execute_mock.assert_not_called()

    def test_stop_after_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=0.1)
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

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=0.1)
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

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=0.1)
        waiter.wait(2)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(2, execute_mock.call_count)

        # noinspection PyUnresolvedReferences
        delta = scope.end - scope.start

        self.assertLessEqual(abs(delta - test_interval), 0.02)

    def test_manual_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=1)
        engine_runner.execute(None)
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

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=0.1)
        waiter.wait(1)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(1, execute_mock.call_count)

    def test_exeption_in_finally_execute(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        logger = Logger()
        logger.finished = Mock(side_effect=Exception("Failed to save"))
        engine_runner = EngineRunner(logger, self.trackers_manager, clients_manager, interval=0.1)
        waiter.wait(1)
        self.assertTrue(waiter.is_set)
        self.assertTrue(engine_runner.is_alive())

        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        self.assertEqual(1, execute_mock.call_count)

    def test_manual_execute_with_ids(self):
        waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=10)
        ids = [1, 2, 3]
        engine_runner.execute(ids)
        waiter.wait(0.3)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        execute_mock.assert_called_once_with(ANY, ids)

    def test_manual_execute_with_ids_ignored_while_in_execute(self):
        waiter = Event()

        long_execute_waiter = Event()

        # noinspection PyUnusedLocal
        def execute(*args, **kwargs):
            waiter.set()
            long_execute_waiter.wait(1)
            self.assertTrue(long_execute_waiter.is_set)

        execute_mock = Mock(side_effect=execute)
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = EngineRunner(Logger(), self.trackers_manager, clients_manager, interval=1)
        engine_runner.execute(None)
        waiter.wait(0.3)
        waiter.clear()
        ids = [1, 2, 3]
        engine_runner.execute(ids)
        long_execute_waiter.set()
        waiter.wait(0.3)
        self.assertTrue(waiter.is_set)
        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())

        execute_mock.assert_called_once_with(ANY, None)


@ddt
class DBExecuteEngineTest(DbTestCase):
    def setUp(self):
        super(DBExecuteEngineTest, self).setUp()
        self.trackers_manager = TrackersManager(TrackerSettings(10, None), {})

    @data(10, 200, 3600, 7200)
    def test_set_interval(self, value):
        execute_mock = Mock()
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})
        engine_runner = DBEngineRunner(Logger(), self.trackers_manager, clients_manager)

        self.assertEqual(7200, engine_runner.interval)

        engine_runner.interval = value

        engine_runner.stop()
        engine_runner.join(1)
        self.assertFalse(engine_runner.is_alive())
        engine_runner = DBEngineRunner(Logger(), self.trackers_manager, clients_manager)

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
        execute_mock = Mock()
        self.trackers_manager.execute = execute_mock
        clients_manager = ClientsManager({})

        self.TestDatetime.mock_now = datetime.now(pytz.utc)

        with patch('monitorrent.engine.datetime', self.TestDatetime(2015, 8, 28)):
            engine_runner = DBEngineRunner(Logger(), self.trackers_manager, clients_manager)

            self.assertIsNone(engine_runner.last_execute)

            engine_runner.execute(None)
            sleep(0.1)

            engine_runner.stop()
            engine_runner.join(1)
            self.assertFalse(engine_runner.is_alive())
            engine_runner = DBEngineRunner(Logger(), self.trackers_manager, clients_manager)

            self.assertEqual(self.TestDatetime.mock_now, engine_runner.last_execute)

            engine_runner.stop()
            engine_runner.join(1)
            self.assertFalse(engine_runner.is_alive())


class TestDbLoggerWrapper(DbTestCase):
    def test_engine_entry_finished(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)

        db_logger.started(finish_time)
        db_logger.finished(finish_time, None)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'finished')
        self.assertIsNone(execute.failed_message)

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, None)
        inner_logger.info.assert_not_called()
        inner_logger.failed.assert_not_called()
        inner_logger.downloaded.assert_not_called()

    def test_engine_entry_failed(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)
        exception = Exception('Some failed exception')

        db_logger.started(finish_time)
        db_logger.finished(finish_time, exception)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'failed')
        self.assertEqual(execute.failed_message, str(exception))

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, exception)
        inner_logger.info.assert_not_called()
        inner_logger.failed.assert_not_called()
        inner_logger.downloaded.assert_not_called()

    def test_engine_entry_log_infos(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)
        message1 = u'Message 1'
        message2 = u'Message 2'

        db_logger.started(finish_time)
        downloaded_time = datetime.now(pytz.utc)
        db_logger.info(message1)
        db_logger.info(message2)
        db_logger.finished(finish_time, None)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'finished')
        self.assertIsNone(execute.failed_message)

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, None)
        inner_logger.info.assert_has_calls([call(message1), call(message2)])
        inner_logger.failed.assert_not_called()
        inner_logger.downloaded.assert_not_called()

        with DBSession() as db:
            entries = db.query(ExecuteLog).all()
            db.expunge_all()

        self.assertEqual(len(entries), 2)

        self.assertEqual(entries[0].message, message1)
        self.assertEqual(entries[1].message, message2)

        # 1 seconds is enought precision for call and log results
        self.assertAlmostEqual(entries[0].time, downloaded_time, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[1].time, downloaded_time, delta=timedelta(seconds=1))

        self.assertEqual(entries[0].level, 'info')
        self.assertEqual(entries[1].level, 'info')

        self.assertEqual(entries[0].execute_id, execute.id)
        self.assertEqual(entries[1].execute_id, execute.id)

    def test_engine_entry_log_failed(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)
        message1 = u'Failed 1'
        message2 = u'Failed 2'

        db_logger.started(finish_time)
        downloaded_time = datetime.now(pytz.utc)
        db_logger.failed(message1)
        db_logger.failed(message2)
        db_logger.finished(finish_time, None)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'finished')
        self.assertIsNone(execute.failed_message)

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, None)
        inner_logger.info.assert_not_called()
        inner_logger.failed.assert_has_calls([call(message1), call(message2)])
        inner_logger.downloaded.assert_not_called()

        with DBSession() as db:
            entries = db.query(ExecuteLog).all()
            db.expunge_all()

        self.assertEqual(len(entries), 2)

        self.assertEqual(entries[0].message, message1)
        self.assertEqual(entries[1].message, message2)

        # 1 seconds is enought precision for call and log results
        self.assertAlmostEqual(entries[0].time, downloaded_time, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[1].time, downloaded_time, delta=timedelta(seconds=1))

        self.assertEqual(entries[0].level, 'failed')
        self.assertEqual(entries[1].level, 'failed')

        self.assertEqual(entries[0].execute_id, execute.id)
        self.assertEqual(entries[1].execute_id, execute.id)

    def test_engine_entry_log_downloaded(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)
        message1 = u'Downloaded 1'
        message2 = u'Downloaded 2'

        db_logger.started(finish_time)
        downloaded_time = datetime.now(pytz.utc)
        db_logger.downloaded(message1, None)
        db_logger.downloaded(message2, None)
        db_logger.finished(finish_time, None)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'finished')
        self.assertIsNone(execute.failed_message)

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, None)
        inner_logger.info.assert_not_called()
        inner_logger.failed.assert_not_called()
        inner_logger.downloaded.assert_has_calls([call(message1, None), call(message2, None)])

        with DBSession() as db:
            entries = db.query(ExecuteLog).all()
            db.expunge_all()

        self.assertEqual(len(entries), 2)

        self.assertEqual(entries[0].message, message1)
        self.assertEqual(entries[1].message, message2)

        # 1 seconds is enought precision for call and log results
        self.assertAlmostEqual(entries[0].time, downloaded_time, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[1].time, downloaded_time, delta=timedelta(seconds=1))

        self.assertEqual(entries[0].level, 'downloaded')
        self.assertEqual(entries[1].level, 'downloaded')

        self.assertEqual(entries[0].execute_id, execute.id)
        self.assertEqual(entries[1].execute_id, execute.id)

    def test_engine_entry_log_mixed(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time = datetime.now(pytz.utc)
        message1 = u'Inf 1'
        message2 = u'Downloaded 1'
        message3 = u'Failed 1'

        db_logger.started(finish_time)
        entry_time = datetime.now(pytz.utc)
        db_logger.info(message1)
        db_logger.downloaded(message2, None)
        db_logger.failed(message3)
        db_logger.finished(finish_time, None)

        with DBSession() as db:
            execute = db.query(Execute).first()
            db.expunge(execute)

        self.assertEqual(execute.finish_time, finish_time)
        self.assertEqual(execute.status, 'finished')
        self.assertIsNone(execute.failed_message)

        inner_logger.started.assert_called_once_with(finish_time)
        inner_logger.finished.assert_called_once_with(finish_time, None)
        inner_logger.info.assert_called_once_with(message1)
        inner_logger.downloaded.assert_called_once_with(message2, None)
        inner_logger.failed.assert_called_once_with(message3)

        with DBSession() as db:
            entries = db.query(ExecuteLog).all()
            db.expunge_all()

        self.assertEqual(len(entries), 3)

        self.assertEqual(entries[0].message, message1)
        self.assertEqual(entries[1].message, message2)
        self.assertEqual(entries[2].message, message3)

        # 1 seconds is enought precision for call and log results
        self.assertAlmostEqual(entries[0].time, entry_time, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[1].time, entry_time, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[2].time, entry_time, delta=timedelta(seconds=1))

        self.assertEqual(entries[0].level, 'info')
        self.assertEqual(entries[1].level, 'downloaded')
        self.assertEqual(entries[2].level, 'failed')

        self.assertEqual(entries[0].execute_id, execute.id)
        self.assertEqual(entries[1].execute_id, execute.id)
        self.assertEqual(entries[2].execute_id, execute.id)

    def test_engine_entry_log_multiple_executes(self):
        inner_logger = MagicMock()

        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, ExecuteLogManager())

        finish_time_1 = datetime.now(pytz.utc)
        finish_time_2 = finish_time_1 + timedelta(seconds=10)
        message1 = u'Inf 1'
        message2 = u'Downloaded 1'
        message3 = u'Failed 1'
        message4 = u'Failed 2'

        exception = Exception('Some exception message')

        db_logger.started(finish_time_1)
        entry_time_1 = datetime.now(pytz.utc)
        db_logger.info(message1)
        db_logger.downloaded(message2, None)
        db_logger.failed(message3)
        db_logger.finished(finish_time_1, None)

        db_logger.started(finish_time_2)
        entry_time_2 = datetime.now(pytz.utc)
        db_logger.failed(message4)
        db_logger.finished(finish_time_2, exception)

        with DBSession() as db:
            executes = db.query(Execute).all()
            execute1 = executes[0]
            execute2 = executes[1]
            db.expunge_all()

        self.assertEqual(execute1.finish_time, finish_time_1)
        self.assertEqual(execute1.status, 'finished')
        self.assertIsNone(execute1.failed_message)

        self.assertEqual(execute2.finish_time, finish_time_2)
        self.assertEqual(execute2.status, 'failed')
        self.assertEqual(execute2.failed_message, str(exception))

        inner_logger.started.assert_has_calls([call(finish_time_1), call(finish_time_2)])
        inner_logger.finished.assert_has_calls([call(finish_time_1, None), call(finish_time_2, exception)])
        inner_logger.info.assert_called_once_with(message1)
        inner_logger.downloaded.assert_called_once_with(message2, None)
        inner_logger.failed.assert_has_calls([call(message3), call(message4)])

        with DBSession() as db:
            entries = db.query(ExecuteLog).all()
            db.expunge_all()

        self.assertEqual(len(entries), 4)

        self.assertEqual(entries[0].message, message1)
        self.assertEqual(entries[1].message, message2)
        self.assertEqual(entries[2].message, message3)
        self.assertEqual(entries[3].message, message4)

        # 1 seconds is enought precision for call and log results
        self.assertAlmostEqual(entries[0].time, entry_time_1, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[1].time, entry_time_1, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[2].time, entry_time_1, delta=timedelta(seconds=1))
        self.assertAlmostEqual(entries[3].time, entry_time_2, delta=timedelta(seconds=1))

        self.assertEqual(entries[0].level, 'info')
        self.assertEqual(entries[1].level, 'downloaded')
        self.assertEqual(entries[2].level, 'failed')
        self.assertEqual(entries[3].level, 'failed')

        self.assertEqual(entries[0].execute_id, execute1.id)
        self.assertEqual(entries[1].execute_id, execute1.id)
        self.assertEqual(entries[2].execute_id, execute1.id)
        self.assertEqual(entries[3].execute_id, execute2.id)

    def test_remove_old_entries(self):
        inner_logger = Mock()
        settings_manager_mock = Mock()
        settings_manager_mock.remove_logs_interval = 10

        log_manager = ExecuteLogManager()
        log_manager.remove_old_entries = Mock()
        # noinspection PyTypeChecker
        db_logger = DbLoggerWrapper(inner_logger, log_manager, settings_manager_mock)

        finish_time_1 = datetime.now(pytz.utc)

        db_logger.started(finish_time_1)
        db_logger.info(u"Message 1")
        db_logger.finished(finish_time_1, None)

        inner_logger.started.assert_called_once_with(finish_time_1)
        inner_logger.finished.assert_called_once_with(finish_time_1, None)
        inner_logger.info.assert_called_once_with("Message 1")
        inner_logger.downloaded.assert_not_called()
        inner_logger.failed.assert_not_called()

        # noinspection PyUnresolvedReferences
        log_manager.remove_old_entries.assert_called_once_with(10)


class ExecuteLogManagerTest(DbTestCase):
    def test_log_entries(self):
        log_manager = ExecuteLogManager()

        log_manager.started(datetime.now(pytz.utc))
        log_manager.log_entry(u'Message 1', 'info')
        log_manager.log_entry(u'Message 2', 'downloaded')
        log_manager.log_entry(u'Message 3', 'downloaded')
        log_manager.log_entry(u'Message 4', 'failed')
        log_manager.log_entry(u'Message 5', 'failed')
        log_manager.log_entry(u'Message 6', 'failed')
        log_manager.finished(datetime.now(pytz.utc), None)

        entries, count = log_manager.get_log_entries(0, 5)

        self.assertEqual(len(entries), 1)
        self.assertEqual(count, 1)
        self.assertEqual(entries[0]['downloaded'], 2)
        self.assertEqual(entries[0]['failed'], 3)

        execute = entries[0]
        self.assertEqual(execute['status'], 'finished')

    def test_log_entries_paging(self):
        log_manager = ExecuteLogManager()

        finish_time_1 = datetime.now(pytz.utc)
        finish_time_2 = finish_time_1 + timedelta(seconds=10)
        finish_time_3 = finish_time_2 + timedelta(seconds=10)

        log_manager.started(finish_time_1)
        log_manager.log_entry(u'Message 1', 'info')
        log_manager.finished(finish_time_1, None)

        log_manager.started(finish_time_2)
        log_manager.log_entry(u'Download 2', 'downloaded')
        log_manager.finished(finish_time_2, None)

        log_manager.started(finish_time_3)
        log_manager.log_entry(u'Failed 3', 'failed')
        log_manager.finished(finish_time_3, None)

        entries, count = log_manager.get_log_entries(0, 1)

        self.assertEqual(len(entries), 1)
        self.assertEqual(count, 3)
        execute = entries[0]
        self.assertEqual(execute['downloaded'], 0)
        self.assertEqual(execute['failed'], 1)
        self.assertEqual(execute['status'], 'finished')

        entries, count = log_manager.get_log_entries(1, 1)

        self.assertEqual(len(entries), 1)
        self.assertEqual(count, 3)
        execute = entries[0]
        self.assertEqual(execute['downloaded'], 1)
        self.assertEqual(execute['failed'], 0)
        self.assertEqual(execute['status'], 'finished')

        entries, count = log_manager.get_log_entries(2, 1)

        self.assertEqual(len(entries), 1)
        self.assertEqual(count, 3)
        execute = entries[0]
        self.assertEqual(execute['downloaded'], 0)
        self.assertEqual(execute['failed'], 0)
        self.assertEqual(execute['status'], 'finished')

    def test_log_entries_details(self):
        log_manager = ExecuteLogManager()

        message1 = u'Message 1'
        message2 = u'Downloaded 1'
        message3 = u'Failed 1'
        finish_time_1 = datetime.now(pytz.utc)

        log_manager.started(finish_time_1)
        log_manager.log_entry(message1, 'info')
        log_manager.log_entry(message2, 'downloaded')
        log_manager.log_entry(message3, 'failed')
        log_manager.finished(finish_time_1, None)

        entries = log_manager.get_execute_log_details(1)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]['level'], 'info')
        self.assertEqual(entries[1]['level'], 'downloaded')
        self.assertEqual(entries[2]['level'], 'failed')

        self.assertEqual(entries[0]['message'], message1)
        self.assertEqual(entries[1]['message'], message2)
        self.assertEqual(entries[2]['message'], message3)

    def test_log_entries_details_after(self):
        log_manager = ExecuteLogManager()

        message1 = u'Message 1'
        message2 = u'Downloaded 1'
        message3 = u'Failed 1'
        finish_time_1 = datetime.now(pytz.utc)

        log_manager.started(finish_time_1)
        log_manager.log_entry(message1, 'info')

        entries = log_manager.get_execute_log_details(1)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['level'], 'info')
        self.assertEqual(entries[0]['message'], message1)

        log_manager.log_entry(message2, 'downloaded')
        log_manager.log_entry(message3, 'failed')
        log_manager.finished(finish_time_1, None)

        entries = log_manager.get_execute_log_details(1, after=entries[0]['id'])

        self.assertEqual(len(entries), 2)

        self.assertEqual(entries[0]['level'], 'downloaded')
        self.assertEqual(entries[0]['message'], message2)

        self.assertEqual(entries[1]['level'], 'failed')
        self.assertEqual(entries[1]['message'], message3)

    def test_log_entries_details_multiple_execute(self):
        log_manager = ExecuteLogManager()

        message11 = u'Message 1'
        message12 = u'Downloaded 1'
        message13 = u'Failed 1'
        message21 = u'Failed 2'
        message22 = u'Downloaded 2'
        message23 = u'Message 2'
        finish_time_1 = datetime.now(pytz.utc)
        finish_time_2 = datetime.now(pytz.utc) + timedelta(minutes=60)

        log_manager.started(finish_time_1)
        log_manager.log_entry(message11, 'info')
        log_manager.log_entry(message12, 'downloaded')
        log_manager.log_entry(message13, 'failed')
        log_manager.finished(finish_time_1, None)

        log_manager.started(finish_time_2)
        log_manager.log_entry(message21, 'failed')
        log_manager.log_entry(message22, 'downloaded')
        log_manager.log_entry(message23, 'info')
        log_manager.finished(finish_time_2, None)

        entries = log_manager.get_execute_log_details(1)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]['level'], 'info')
        self.assertEqual(entries[1]['level'], 'downloaded')
        self.assertEqual(entries[2]['level'], 'failed')

        self.assertEqual(entries[0]['message'], message11)
        self.assertEqual(entries[1]['message'], message12)
        self.assertEqual(entries[2]['message'], message13)

        entries = log_manager.get_execute_log_details(2)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]['level'], 'failed')
        self.assertEqual(entries[1]['level'], 'downloaded')
        self.assertEqual(entries[2]['level'], 'info')

        self.assertEqual(entries[0]['message'], message21)
        self.assertEqual(entries[1]['message'], message22)
        self.assertEqual(entries[2]['message'], message23)

    def test_started_fail(self):
        log_manager = ExecuteLogManager()

        log_manager.started(datetime.now(pytz.utc))
        with self.assertRaises(Exception):
            log_manager.started(datetime.now(pytz.utc))

    def test_finished_fail(self):
        log_manager = ExecuteLogManager()

        with self.assertRaises(Exception):
            log_manager.finished(datetime.now(pytz.utc), None)

    def test_log_entry_fail(self):
        log_manager = ExecuteLogManager()

        with self.assertRaises(Exception):
            log_manager.log_entry(datetime.now(pytz.utc), 'info')

    def test_is_running(self):
        log_manager = ExecuteLogManager()

        message11 = u'Message 1'
        message12 = u'Downloaded 1'
        message13 = u'Failed 1'
        finish_time_1 = datetime.now(pytz.utc)

        self.assertFalse(log_manager.is_running())

        log_manager.started(finish_time_1)
        log_manager.log_entry(message11, 'info')
        log_manager.log_entry(message12, 'downloaded')
        log_manager.log_entry(message13, 'failed')

        self.assertTrue(log_manager.is_running())
        self.assertTrue(log_manager.is_running(1))
        self.assertFalse(log_manager.is_running(2))

        log_manager.finished(finish_time_1, None)

        self.assertFalse(log_manager.is_running())
        self.assertFalse(log_manager.is_running(1))
        self.assertFalse(log_manager.is_running(2))

        finish_time_2 = datetime.now(pytz.utc) + timedelta(minutes=60)

        log_manager.started(finish_time_2)
        log_manager.log_entry(message11, 'info')
        log_manager.log_entry(message12, 'downloaded')
        log_manager.log_entry(message13, 'failed')

        self.assertTrue(log_manager.is_running())
        self.assertFalse(log_manager.is_running(1))
        self.assertTrue(log_manager.is_running(2))

        log_manager.finished(finish_time_2, None)

    def test_get_current_execute_log_details(self):
        log_manager = ExecuteLogManager()

        message11 = u'Message 1'
        message12 = u'Downloaded 1'
        message13 = u'Failed 1'
        finish_time_1 = datetime.now(pytz.utc)

        self.assertIsNone(log_manager.get_current_execute_log_details())

        log_manager.started(finish_time_1)
        log_manager.log_entry(message11, 'info')

        result = log_manager.get_current_execute_log_details()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['message'], message11)
        self.assertEqual(result[0]['level'], 'info')

        log_manager.log_entry(message12, 'downloaded')
        log_manager.log_entry(message13, 'failed')

        result = log_manager.get_current_execute_log_details(result[0]['id'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['message'], message12)
        self.assertEqual(result[0]['level'], 'downloaded')
        self.assertEqual(result[1]['message'], message13)
        self.assertEqual(result[1]['level'], 'failed')

        log_manager.finished(finish_time_1, None)

        self.assertIsNone(log_manager.get_current_execute_log_details())

    def test_remove_old_entries(self):
        log_manager = ExecuteLogManager()
        now = datetime.now(pytz.utc)

        message11 = u'Message 1'

        start1 = now - timedelta(days=13)
        log_manager.started(start1)
        log_manager.log_entry(message11 + ' 1', 'info')
        log_manager.finished(start1, None)

        start2 = now - timedelta(days=12)
        log_manager.started(start2)
        log_manager.log_entry(message11 + ' 2', 'info')
        log_manager.finished(start2, None)

        start3 = now - timedelta(days=11)
        log_manager.started(start3)
        log_manager.log_entry(message11 + ' 3', 'info')
        log_manager.finished(start3, None)

        # This should be deleted as well it was exactly 10 days before
        start4 = now - timedelta(days=10)
        log_manager.started(start4)
        log_manager.log_entry(message11 + ' 4', 'info')
        log_manager.finished(start4, None)

        start5 = now - timedelta(days=5)
        log_manager.started(start5)
        log_manager.log_entry(message11 + ' 5', 'info')
        log_manager.log_entry(message11 + ' 6', 'info')
        log_manager.finished(start5, None)

        log_manager.remove_old_entries(10)

        entries, count = log_manager.get_log_entries(0, 10)

        self.assertEqual(count, 1)
        self.assertEqual(len(entries), 1)

        self.assertEqual(entries[0]['start_time'], start5)
        self.assertEqual(entries[0]['finish_time'], start5)

        execute_id = entries[0]['id']

        details = log_manager.get_execute_log_details(execute_id)

        self.assertEqual(len(details), 2)

        self.assertEqual(details[0]['level'], 'info')
        self.assertEqual(details[0]['message'], message11 + ' 5')

        self.assertEqual(details[1]['level'], 'info')
        self.assertEqual(details[1]['message'], message11 + ' 6')

    def test_remove_old_entries_keep_all(self):
        log_manager = ExecuteLogManager()
        now = datetime.now(pytz.utc)

        message11 = u'Message 1'

        start1 = now - timedelta(days=9)
        log_manager.started(start1)
        log_manager.log_entry(message11 + ' 1', 'info')
        log_manager.finished(start1, None)

        start2 = now - timedelta(days=8)
        log_manager.started(start2)
        log_manager.log_entry(message11 + ' 2', 'info')
        log_manager.finished(start2, None)

        log_manager.remove_old_entries(10)

        entries, count = log_manager.get_log_entries(0, 10)

        self.assertEqual(count, 2)
        self.assertEqual(len(entries), 2)

        self.assertEqual(entries[0]['start_time'], start2)
        self.assertEqual(entries[0]['finish_time'], start2)

        self.assertEqual(entries[1]['start_time'], start1)
        self.assertEqual(entries[1]['finish_time'], start1)

        execute_id = entries[0]['id']

        details = log_manager.get_execute_log_details(execute_id)

        self.assertEqual(len(details), 1)

        self.assertEqual(details[0]['level'], 'info')
        self.assertEqual(details[0]['message'], message11 + ' 2')

        execute_id = entries[1]['id']

        details = log_manager.get_execute_log_details(execute_id)

        self.assertEqual(len(details), 1)

        self.assertEqual(details[0]['level'], 'info')
        self.assertEqual(details[0]['message'], message11 + ' 1')
