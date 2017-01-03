from builtins import str
from collections import OrderedDict

from ddt import ddt, data
from mock import Mock, MagicMock, patch
from sqlalchemy import Column, Integer, ForeignKey
from monitorrent.db import DBSession, row2dict
from monitorrent.plugins.trackers import Topic
from monitorrent.plugins.status import Status
from tests import TestCase, DbTestCase
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, TrackerSettings
from monitorrent.plugin_managers import TrackersManager

TRACKER1_PLUGIN_NAME = 'tracker1.com'
TRACKER2_PLUGIN_NAME = 'tracker2.com'


class Tracker1Topic(Topic):
    __tablename__ = "tracker1_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    some_addition_field = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': TRACKER1_PLUGIN_NAME
    }


class Tracker2Topic(Topic):
    __tablename__ = "tracker2_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    some_addition_field = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': TRACKER2_PLUGIN_NAME
    }


class Tracker1(TrackerPluginBase):
    topic_class = Tracker1Topic

    def execute(self, ids, engine):
        pass

    def parse_url(self, url):
        pass

    def can_parse_url(self, url):
        pass

    def _prepare_request(self, topic):
        pass


# noinspection PyAbstractClass
class Tracker2(WithCredentialsMixin, TrackerPluginBase):
    topic_class = Tracker2Topic

    def parse_url(self, url):
        pass

    def can_parse_url(self, url):
        pass

    def _prepare_request(self, topic):
        pass

    def login(self):
        pass

    def verify(self):
        pass


class TrackersManagerTest(TestCase):
    def setUp(self):
        super(TrackersManagerTest, self).setUp()
        self.tracker1 = Tracker1()
        self.tracker2 = Tracker2()

        tracker_settings = TrackerSettings(10, None)
        settings_manager = Mock()
        settings_manager.tracker_settings = tracker_settings

        # noinspection PyTypeChecker
        self.trackers_manager = TrackersManager(settings_manager, OrderedDict((
            (TRACKER1_PLUGIN_NAME, self.tracker1),
            (TRACKER2_PLUGIN_NAME, self.tracker2))
        ))

    def test_get_settings(self):
        self.assertIsNone(self.trackers_manager.get_settings(TRACKER1_PLUGIN_NAME))

        credentials2 = {'login': 'username'}
        get_credentials_mock = MagicMock(return_value=credentials2)
        self.tracker2.get_credentials = get_credentials_mock

        self.assertEqual(self.trackers_manager.get_settings(TRACKER2_PLUGIN_NAME), credentials2)

        get_credentials_mock.assert_called_with()

    def test_set_settings(self):
        credentials1 = {'login': 'username'}
        self.assertFalse(self.trackers_manager.set_settings(TRACKER1_PLUGIN_NAME, credentials1))

        credentials2 = {'login': 'username', 'password': 'password'}
        update_credentials_mock2 = MagicMock()
        self.tracker2.update_credentials = update_credentials_mock2

        self.assertTrue(self.trackers_manager.set_settings(TRACKER2_PLUGIN_NAME, credentials2))

        update_credentials_mock2.assert_called_with(credentials2)

    def test_check_connection(self):
        self.assertFalse(self.trackers_manager.check_connection(TRACKER1_PLUGIN_NAME))

        verify_mock = MagicMock(return_value=True)
        self.tracker2.verify = verify_mock

        self.assertTrue(self.trackers_manager.check_connection(TRACKER2_PLUGIN_NAME))

        verify_mock.assert_called_with()

    def test_prepare_add_topic_1(self):
        parsed_url = {'display_name': "Some Name / Translated Name"}
        prepare_add_topic_mock1 = MagicMock(return_value=parsed_url)
        self.tracker1.prepare_add_topic = prepare_add_topic_mock1
        result = self.trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNotNone(result)

        prepare_add_topic_mock1.assert_called_with('http://tracker.com/1/')

        self.assertEqual(result, {'form': TrackerPluginBase.topic_form, 'settings': parsed_url})

    def test_prepare_add_topic_2(self):
        prepare_add_topic_mock1 = MagicMock(return_value=None)
        self.tracker1.prepare_add_topic = prepare_add_topic_mock1

        parsed_url = {'display_name': "Some Name / Translated Name"}
        prepare_add_topic_mock2 = MagicMock(return_value=parsed_url)
        self.tracker2.prepare_add_topic = prepare_add_topic_mock2

        result = self.trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNotNone(result)

        prepare_add_topic_mock1.assert_called_with('http://tracker.com/1/')
        prepare_add_topic_mock2.assert_called_with('http://tracker.com/1/')

        self.assertEqual(result, {'form': TrackerPluginBase.topic_form, 'settings': parsed_url})

    def test_prepare_add_topic_3(self):
        prepare_add_topic_mock1 = MagicMock(return_value=None)
        self.tracker1.prepare_add_topic = prepare_add_topic_mock1

        prepare_add_topic_mock2 = MagicMock(return_value=None)
        self.tracker2.prepare_add_topic = prepare_add_topic_mock2

        result = self.trackers_manager.prepare_add_topic('http://tracker.com/1/')
        self.assertIsNone(result)

        prepare_add_topic_mock1.assert_called_with('http://tracker.com/1/')
        prepare_add_topic_mock2.assert_called_with('http://tracker.com/1/')

    def test_add_topic_1(self):
        can_parse_url_mock1 = MagicMock(return_value=True)
        add_topic_mock1 = MagicMock(return_value=True)
        self.tracker1.can_parse_url = can_parse_url_mock1
        self.tracker1.add_topic = add_topic_mock1

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertTrue(self.trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_called_with(url, params)

    def test_add_topic_2(self):
        can_parse_url_mock1 = MagicMock(return_value=False)
        add_topic_mock1 = MagicMock(return_value=False)
        self.tracker1.can_parse_url = can_parse_url_mock1
        self.tracker1.add_topic = add_topic_mock1

        can_parse_url_mock2 = MagicMock(return_value=True)
        add_topic_mock2 = MagicMock(return_value=True)
        self.tracker2.can_parse_url = can_parse_url_mock2
        self.tracker2.add_topic = add_topic_mock2

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertTrue(self.trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_not_called()

        can_parse_url_mock2.assert_called_with(url)
        add_topic_mock2.assert_called_with(url, params)

    def test_add_topic_3(self):
        can_parse_url_mock1 = MagicMock(return_value=False)
        add_topic_mock1 = MagicMock(return_value=False)
        self.tracker1.can_parse_url = can_parse_url_mock1
        self.tracker1.add_topic = add_topic_mock1

        can_parse_url_mock2 = MagicMock(return_value=False)
        add_topic_mock2 = MagicMock(return_value=False)
        self.tracker2.can_parse_url = can_parse_url_mock2
        self.tracker2.add_topic = add_topic_mock2

        params = {'display_name': "Some Name / Translated Name"}
        url = 'http://tracker.com/1/'
        self.assertFalse(self.trackers_manager.add_topic(url, params))

        can_parse_url_mock1.assert_called_with(url)
        add_topic_mock1.assert_not_called()

        can_parse_url_mock2.assert_called_with(url)
        add_topic_mock2.assert_not_called()


@ddt
class TrackersManagerDbPartTest(DbTestCase):
    DISPLAY_NAME1 = "Some Name / Translated Name"
    URL1 = "http://tracker.com/1/"

    def setUp(self):
        super(TrackersManagerDbPartTest, self).setUp()

        with DBSession() as db:
            topic = Tracker1Topic(display_name=self.DISPLAY_NAME1,
                                  url=self.URL1,
                                  type=TRACKER1_PLUGIN_NAME,
                                  some_addition_field=1)
            db.add(topic)
            db.commit()
            self.tracker1_id1 = topic.id

        self.tracker1 = Tracker1()
        self.tracker2 = Tracker2()

        tracker_settings = TrackerSettings(10, None)
        settings_manager = Mock()
        settings_manager.tracker_settings = tracker_settings

        # noinspection PyTypeChecker
        self.trackers_manager = TrackersManager(settings_manager, {
            TRACKER1_PLUGIN_NAME: self.tracker1,
            TRACKER2_PLUGIN_NAME: self.tracker2,
        })

    def create_removed_topic(self):
        remove_type = TRACKER1_PLUGIN_NAME + ".uk"
        with DBSession() as db:
            topic = Topic(display_name=self.DISPLAY_NAME1 + " / Test",
                          url="http://tracker.com/2/",
                          type=remove_type)
            result = db.execute(topic.__table__.insert(), row2dict(topic, fields=['display_name', 'url', 'type']))
            tracker1_id2 = result.inserted_primary_key[0]
        return tracker1_id2

    def test_remove_topic_1(self):
        self.assertTrue(self.trackers_manager.remove_topic(self.tracker1_id1))
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == self.tracker1_id1).first()
            self.assertIsNone(topic)

    def test_remove_topic_2(self):
        with self.assertRaises(KeyError):
            self.trackers_manager.remove_topic(self.tracker1_id1 + 1)
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == self.tracker1_id1).first()
            self.assertIsNotNone(topic)

    def test_get_topic_1(self):
        topic_settings = {'display_name': self.DISPLAY_NAME1}
        get_topic_mock = MagicMock(return_value=topic_settings)
        self.tracker1.get_topic = get_topic_mock

        result = self.trackers_manager.get_topic(self.tracker1_id1)

        self.assertEqual({'form': self.tracker1.topic_form, 'settings': topic_settings}, result)

        get_topic_mock.assert_called_with(self.tracker1_id1)

    def test_get_topic_2(self):
        with self.assertRaises(KeyError):
            self.trackers_manager.get_topic(self.tracker1_id1 + 1)

    def test_get_topic_3(self):
        tracker1_id2 = self.create_removed_topic()

        with self.assertRaises(KeyError):
            self.trackers_manager.get_topic(tracker1_id2)

    @data(True, False)
    def test_update_topic_1(self, value):
        topic_settings = {'display_name': self.DISPLAY_NAME1}
        update_topic_mock = MagicMock(return_value=value)
        self.tracker1.update_topic = update_topic_mock

        self.assertEqual(value, self.trackers_manager.update_topic(self.tracker1_id1, topic_settings))

        update_topic_mock.assert_called_with(self.tracker1_id1, topic_settings)

    def test_update_topic_2(self):
        tracker1_id2 = self.create_removed_topic()

        with self.assertRaises(KeyError):
            self.trackers_manager.get_topic(tracker1_id2)

    def test_reset_topic_status_1(self):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == self.tracker1_id1).first()
            topic.status = Status.NotFound
        topic = self.trackers_manager.get_watching_topics()[0]
        self.assertEqual(topic['status'], str(Status.NotFound))

        self.trackers_manager.reset_topic_status(self.tracker1_id1)
        topic = self.trackers_manager.get_watching_topics()[0]
        self.assertEqual(topic['status'], str(Status.Ok))

    def test_reset_topic_status_2(self):
        tracker1_id2 = self.tracker1_id1 * 100

        with self.assertRaises(KeyError):
            self.trackers_manager.reset_topic_status(tracker1_id2)

    def test_set_topic_paused_success(self):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == self.tracker1_id1).first()
            topic.paused = True
        topic = self.trackers_manager.get_watching_topics()[0]
        self.assertEqual(topic['paused'], True)

        self.trackers_manager.set_topic_paused(self.tracker1_id1, False)
        topic = self.trackers_manager.get_watching_topics()[0]
        self.assertEqual(topic['paused'], False)

        self.trackers_manager.set_topic_paused(self.tracker1_id1, True)
        topic = self.trackers_manager.get_watching_topics()[0]
        self.assertEqual(topic['paused'], True)

    def test_reset_topic_status_failed(self):
        tracker1_id2 = self.tracker1_id1 * 100

        with self.assertRaises(KeyError):
            self.trackers_manager.set_topic_paused(tracker1_id2, True)

    def test_get_watching_topics_1(self):
        topics = self.trackers_manager.get_watching_topics()

        self.assertIsNotNone(topics)
        self.assertEqual(1, len(topics))
        self.assertEqual([
            {
                'id': self.tracker1_id1,
                'display_name': self.DISPLAY_NAME1,
                'url': self.URL1,
                'last_update': None,
                'info': None,
                'tracker': TRACKER1_PLUGIN_NAME,
                'status': Status.Ok.__str__(),
                'paused': False
            }],
            topics)

    def test_get_watching_topics_2(self):
        self.create_removed_topic()

        topics = self.trackers_manager.get_watching_topics()

        self.assertIsNotNone(topics)
        self.assertEqual(1, len(topics))
        self.assertEqual([
            {
                'id': self.tracker1_id1,
                'display_name': self.DISPLAY_NAME1,
                'url': self.URL1,
                'last_update': None,
                'info': None,
                'tracker': TRACKER1_PLUGIN_NAME,
                'status': Status.Ok.__str__(),
                'paused': False
            }],
            topics)

    def test_get_tracker_topics(self):
        topics = self.trackers_manager.get_tracker_topics(TRACKER1_PLUGIN_NAME)

        self.assertIsNotNone(topics)
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0].id, self.tracker1_id1)

        topics = self.trackers_manager.get_tracker_topics(TRACKER2_PLUGIN_NAME)

        self.assertEqual(topics, [])

    def test_get_tracker_topics_key_error(self):
        topics = self.trackers_manager.get_tracker_topics(TRACKER1_PLUGIN_NAME)

        self.assertIsNotNone(topics)
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0].id, self.tracker1_id1)

        with self.assertRaises(KeyError):
            self.trackers_manager.get_tracker_topics('UnknowTracker')

    def test_get_status_topics(self):
        with DBSession() as db:
            topic1 = Tracker1Topic(display_name=self.DISPLAY_NAME1 + '/1',
                                   url=self.URL1 + '/1',
                                   type=TRACKER1_PLUGIN_NAME,
                                   some_addition_field=1,
                                   status=Status.Error)
            db.add(topic1)
            topic2 = Tracker1Topic(display_name=self.DISPLAY_NAME1 + '/2',
                                   url=self.URL1 + '/2',
                                   type=TRACKER1_PLUGIN_NAME,
                                   some_addition_field=1,
                                   status=Status.NotFound)
            db.add(topic2)
            topic3 = Tracker2Topic(display_name=self.DISPLAY_NAME1 + '/3',
                                   url=self.URL1 + '/3',
                                   type=TRACKER2_PLUGIN_NAME,
                                   some_addition_field=1,
                                   status=Status.Unknown)
            db.add(topic3)
            db.commit()

            topic1_id = topic1.id
            topic2_id = topic2.id
            topic3_id = topic3.id

        topics = self.trackers_manager.get_status_topics_ids([Status.Ok])

        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], self.tracker1_id1)

        topics = self.trackers_manager.get_status_topics_ids([Status.Error])

        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], topic1_id)

        topics = self.trackers_manager.get_status_topics_ids([Status.NotFound])

        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], topic2_id)

        topics = self.trackers_manager.get_status_topics_ids([Status.Unknown])

        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], topic3_id)

        topics = self.trackers_manager.get_status_topics_ids([Status.Error, Status.NotFound])

        self.assertEqual(len(topics), 2)
        self.assertListEqual(sorted(topics), sorted([topic1_id, topic2_id]))
