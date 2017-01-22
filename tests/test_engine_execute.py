# coding=utf-8
import datetime
from ddt import ddt
from mock import Mock, MagicMock, call, ANY

from tests import TestCase, ReadContentMixin
from sqlalchemy import Column, Integer, ForeignKey, String

from monitorrent.utils.bittorrent_ex import Torrent
from monitorrent.engine import Engine, EngineExecute, EngineTrackers, EngineTracker, \
    EngineTopics, EngineTopic, EngineDownloads, Logger
from monitorrent.plugins import Topic
from monitorrent.plugins.status import Status
from monitorrent.plugins.clients import TopicSettings
from monitorrent.plugins.trackers import TrackerPluginBase
from monitorrent.plugin_managers import ClientsManager, TrackersManager, NotifierManager
from monitorrent.settings_manager import SettingsManager


class MockSettingsManager(SettingsManager):
    _settings = dict()

    @staticmethod
    def _set_settings(name, value):
        MockSettingsManager._settings[name] = value

    @staticmethod
    def _get_settings(name, default=None):
        return MockSettingsManager._settings.get(name, default)


@ddt
class EngineTest(TestCase):
    def setUp(self):
        super(EngineTest, self).setUp()

        self.log_mock = Logger()
        self.log_info_mock = Mock()
        self.log_downloaded_mock = Mock()
        self.log_failed_mock = Mock()

        self.log_mock.info = self.log_info_mock
        self.log_mock.downloaded = self.log_downloaded_mock
        self.log_mock.failed = self.log_failed_mock

        self.settings_manager = MockSettingsManager()
        self.trackers_manager = TrackersManager(self.settings_manager, {})
        self.clients_manager = ClientsManager({'mock': MockClient()})
        self.notifier_manager = MagicMock()

        self.clients_manager.set_default('mock')

        self.engine = Engine(self.log_mock, self.settings_manager, self.trackers_manager,
                             self.clients_manager, self.notifier_manager)


class EngineExecuteTest(EngineTest):
    def test_execute_trackers(self):
        topics = [Topic()]

        tracker = Mock()
        tracker.name = 'test.com'
        tracker.init = Mock()
        tracker.get_topics = Mock(return_value=topics)
        tracker.execute = Mock()

        self.trackers_manager.trackers = {'test.com': tracker}

        self.engine.execute(None)

        tracker.init.assert_called_once()
        tracker.execute.assert_called_once_with(topics, ANY)

    def test_empty_execute(self):
        topics = []

        tracker = Mock()
        tracker.name = 'test.com'
        tracker.init = Mock()
        tracker.get_topics = Mock(return_value=topics)
        tracker.execute = Mock()

        self.trackers_manager.trackers = {'test.com': tracker}

        self.engine.execute(None)

        tracker.init.assert_not_called()
        tracker.execute.assert_not_called()


class EngineExecute2Test(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_execute = EngineExecute(self.engine, self.notifier_manager_execute)

    def test_call_info_should_delegate_to_engine_info(self):
        message = "Test Message"
        self.engine_execute.info(message)

        self.engine.info.assert_called_once_with(message)
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

        self.notifier_manager_execute.notify.assert_not_called()

    def test_call_failed_should_delegate_to_engine_failed_and_notify(self):
        message = "Test Message"
        self.engine_execute.failed(message)

        self.engine.info.assert_not_called()
        self.engine.failed.assert_called_once_with(message, None, None, None)
        self.engine.downloaded.assert_not_called()

        self.notifier_manager_execute.notify_failed.assert_called_once_with(message)

    def test_call_downloaded_should_delegate_to_engine_downloaded_and_notify(self):
        message = "Test Message"
        torrent = object()
        self.engine_execute.downloaded(message, torrent)

        self.engine.info.assert_not_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_called_once_with(message, torrent)

        self.notifier_manager_execute.notify_download.assert_called_once_with(message)

    def test_call_failed_with_failed_notify_should_not_crash(self):
        message = u"Test Message"
        error_message = u"Some error"
        exception = Exception(error_message)
        self.notifier_manager_execute.notify_failed = Mock(side_effect=exception)

        self.engine_execute.failed(message)

        self.engine.info.assert_not_called()
        assert self.engine.failed.call_count == 2
        self.engine.downloaded.assert_not_called()

        self.notifier_manager_execute.notify_failed.assert_called_once_with(message)

        assert message in self.engine.failed.mock_calls[0][1][0]
        assert exception == self.engine.failed.mock_calls[1][1][2]

    def test_call_downloaded_with_failed_notify_should_not_crash(self):
        message = u"Test Message"
        error_message = u"Some error"
        torrent = object()
        exception = Exception(error_message)
        self.notifier_manager_execute.notify_download = Mock(side_effect=exception)

        self.engine_execute.downloaded(message, torrent)

        self.engine.info.assert_not_called()
        assert self.engine.failed.call_count == 1
        self.engine.downloaded.assert_called_once_with(message, torrent)

        self.notifier_manager_execute.notify_download.assert_called_once_with(message)

        assert exception == self.engine.failed.mock_calls[0][1][2]


class EngineTrackersTest(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_trackers = EngineTrackers({'tracker': 1}, self.notifier_manager_execute, self.engine)

    def test_regular_exit_should_call_info(self):
        with self.engine_trackers:
            pass

        self.engine.info.assert_has_calls([call(u'Begin execute'), call(u'End execute')])
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_exit_should_call_failed_and_not_crash(self):
        error_message = u"Some error"
        exception = Exception(error_message)

        with self.engine_trackers:
            raise exception

        self.engine.info.assert_called_once_with(u'Begin execute')
        assert exception == self.engine.failed.mock_calls[0][1][2]
        self.engine.downloaded.assert_not_called()


class EngineTrackerTest(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.engine_trackers = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_tracker = EngineTracker('tracker', self.engine_trackers,
                                            self.notifier_manager_execute, self.engine)

    def test_execute(self):
        with self.engine_tracker.start(2) as engine_topics:
            with engine_topics.start(0, "Topic 1"):
                pass

            with engine_topics.start(1, "Topic 2"):
                pass

        self.engine.info.assert_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_regular_exit_should_call_info(self):
        with self.engine_tracker:
            pass

        self.engine.info.assert_has_calls([call(u'Start checking for <b>tracker</b>'),
                                           call(u'End checking for <b>tracker</b>')])
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_exit_should_call_failed_and_not_crash(self):
        error_message = u"Some error"
        exception = Exception(error_message)

        with self.engine_tracker:
            raise exception

        self.engine.info.assert_called_once_with(u'Start checking for <b>tracker</b>')
        assert exception == self.engine.failed.mock_calls[0][1][2]
        self.engine.downloaded.assert_not_called()


class TestEngineTopics(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.engine_tracker = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_topics = EngineTopics(1, self.engine_tracker, self.notifier_manager_execute, self.engine)

    def test_regular_exit_should_not_call_info(self):
        with self.engine_topics:
            pass

        self.engine.info.assert_not_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_exit_should_call_failed_and_not_crash(self):
        error_message = u"Some error"
        exception = Exception(error_message)

        with self.engine_topics:
            raise exception

        self.engine.info.assert_not_called()
        assert exception == self.engine.failed.mock_calls[0][1][2]
        self.engine.downloaded.assert_not_called()


class TestEngineTopic(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.engine_topics = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_topic = EngineTopic(u"Topic", self.engine_topics, self.notifier_manager_execute, self.engine)

    def test_regular_exit_should_not_call_info(self):
        with self.engine_topic:
            pass

        self.engine.info.assert_has_calls([call(u'Check for changes <b>Topic</b>')])
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_exit_should_call_failed_and_not_crash(self):
        error_message = u"Some error"
        exception = Exception(error_message)

        with self.engine_topic:
            raise exception

        self.engine.info.assert_has_calls([call(u'Check for changes <b>Topic</b>')])
        assert exception == self.engine.failed.mock_calls[0][1][2]
        self.engine.downloaded.assert_not_called()


class TestEngineDownloads(TestCase):
    def setUp(self):
        self.engine = Mock()
        self.engine_topic = Mock()
        self.notifier_manager_execute = Mock()

        # noinspection PyTypeChecker
        self.engine_downloads = EngineDownloads(1, self.engine_topic, self.notifier_manager_execute, self.engine)

    def test_regular_exit_should_not_call_info(self):
        with self.engine_downloads:
            pass

        self.engine.info.assert_not_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_exit_should_call_failed_and_not_crash(self):
        error_message = u"Some error"
        exception = Exception(error_message)

        with self.engine_downloads:
            raise exception

        self.engine.info.assert_not_called()
        assert self.engine.failed.mock_calls[0][1][2] == exception
        self.engine.downloaded.assert_not_called()


class MockTopic(Topic):
    __tablename__ = "execute_mock_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': "mocktracker.com"
    }


class MockClient(object):
    def __init__(self):
        self.added_hash = None

    def get_settings(self):
        return {}

    def set_settings(self, settings):
        pass

    def check_connection(self):
        return True

    def find_torrent(self, torrent_hash):
        if self.added_hash == torrent_hash:
            return {'date_added': datetime.datetime.utcnow(), 'name': 'file'}
        return None

    def add_torrent(self, torrent_content, torrent_settings):
        torrent = Torrent(torrent_content)
        self.added_hash = torrent.info_hash
        return True

    def remove_torrent(self, torrent_hash):
        return True


class MockTracker(TrackerPluginBase, ReadContentMixin):
    topic_class = MockTopic
    name = 'mocktracker.com'

    def __init__(self):
        filename = self.get_httpretty_filename('Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent')
        self.torrent = Torrent.from_file(filename)

    def _prepare_request(self, topic):
        return topic.url

    def can_parse_url(self, url):
        raise NotImplemented()

    def parse_url(self, url):
        raise NotImplemented()

    def execute(self, topics, engine):
        """
        :type engine: EngineTracker
        """
        with engine.start(len(topics)) as engine_topics:
            for i in range(0, len(topics)):
                topic = topics[i]
                topic_name = topic.display_name
                with engine_topics.start(i, topic_name) as engine_topic:
                    engine_topic.status_changed(Status.Error, Status.Ok)
                    with engine_topic.start(1) as engine_downloads:
                        engine_downloads.downloaded(u"<b>{0}</b> was changed".format(topic_name), self.torrent)
                        engine_downloads.add_torrent(0, u"file.torrent", self.torrent, None,
                                                     TopicSettings(None))


class EngineExecuteFullTest(EngineTest):
    def test_execute(self):
        topics = [Topic(id=1, url='http://mocktracker.com/topic/id123', display_name=u'Show / Шоу')]

        tracker = MockTracker()
        tracker.get_topics = Mock(return_value=topics)

        self.trackers_manager.trackers = {'mocktracker.com': tracker}

        self.engine.info = Mock(side_effect=self.engine.info)
        self.engine.failed = Mock(side_effect=self.engine.failed)
        self.engine.downloaded = Mock(side_effect=self.engine.downloaded)

        self.engine.execute(None)

        self.engine.info.assert_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_called_once_with(u'<b>Show / Шоу</b> was changed', ANY)

    def test_exception_during_engine_execute_should_be_handled_and_logged(self):
        topics = [Topic(id=1, url='http://mocktracker.com/topic/id123', display_name=u'Show / Шоу')]

        tracker = MockTracker()
        tracker.get_topics = Mock(return_value=topics)
        tracker.init = Mock(side_effect=Exception)

        self.trackers_manager.trackers = {'mocktracker.com': tracker}

        self.engine.info = Mock(side_effect=self.engine.info)
        self.engine.failed = Mock(side_effect=self.engine.failed)
        self.engine.downloaded = Mock(side_effect=self.engine.downloaded)

        self.engine.execute(None)

        self.engine.info.assert_called()
        self.engine.failed.assert_called()
        self.engine.downloaded.assert_not_called()

    def test_exception_during_tracker_execute_should_be_handled_and_logged(self):
        topics = [Topic(id=1, url='http://mocktracker.com/topic/id123', display_name=u'Show / Шоу')]

        tracker = MockTracker()
        tracker.get_topics = Mock(return_value=topics)
        tracker.execute = Mock(side_effect=Exception)

        self.trackers_manager.trackers = {'mocktracker.com': tracker}

        self.engine.info = Mock(side_effect=self.engine.info)
        self.engine.failed = Mock(side_effect=self.engine.failed)
        self.engine.downloaded = Mock(side_effect=self.engine.downloaded)

        self.engine.execute(None)

        self.engine.info.assert_called()
        self.engine.failed.assert_called()
        self.engine.downloaded.assert_not_called()
