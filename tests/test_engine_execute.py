# coding=utf-8
import datetime
from ddt import ddt
from mock import Mock, MagicMock, call, ANY

from tests import TestCase, ReadContentMixin
from sqlalchemy import Column, Integer, ForeignKey, String

from monitorrent.utils.bittorrent import Torrent
from monitorrent.engine import Engine, EngineTracker, Logger
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


class EngineTrackerTest(EngineTest):
    def test_execute(self):
        engine_trackers = Mock()
        engine = Mock()

        # noinspection PyTypeChecker
        engine_tracker = EngineTracker("tracker", engine_trackers, None, engine)

        with engine_tracker.start(2) as engine_topics:
            with engine_topics.start(0, "Topic 1"):
                pass

            with engine_topics.start(1, "Topic 2"):
                pass


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

        self.engine.info = Mock()
        self.engine.failed = Mock()
        self.engine.downloaded = Mock()

        self.engine.execute(None)

        self.engine.info.assert_called()
        self.engine.failed.assert_not_called()
        self.engine.downloaded.assert_called_once_with(u'<b>Show / Шоу</b> was changed', ANY)
