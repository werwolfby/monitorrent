from ddt import ddt
from mock import Mock, ANY

from plugin_managers import NotifierManager
from tests import TestCase
from sqlalchemy import Column, Integer, ForeignKey, String

from monitorrent.engine import Engine, EngineTracker, Logger
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, ExecuteWithHashChangeMixin
from monitorrent.plugin_managers import ClientsManager, TrackersManager
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
        self.trackers_manager = TrackersManager(self.settings_manager)
        self.clients_manager = ClientsManager()
        self.notifier_manager = NotifierManager({})

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

        self.trackers_manager.trackers['test.com'] = tracker

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


class MockTracker(ExecuteWithHashChangeMixin, TrackerPluginBase):
    topic_class = MockTopic
    name = "mocktracker.com"

    def _prepare_request(self, topic):
        return topic.url

    def can_parse_url(self, url):
        raise NotImplemented()

    def parse_url(self, url):
        raise NotImplemented()


class EngineExecuteFullTest(EngineTest):
    def test_execute(self):
        topics = [Topic(id=1, url='http://mocktracker.com/topic/id123')]

        tracker = MockTracker()
        tracker.get_topics = Mock(return_value=topics)

        self.trackers_manager.trackers['mocktracker.com'] = tracker

        self.engine.execute(None)
































