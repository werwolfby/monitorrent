from datetime import datetime
import six
import pytz
from requests import Response
from sqlalchemy import Column, Integer, String, ForeignKey
from ddt import ddt, data, unpack
from mock import patch, Mock, MagicMock, ANY
from monitorrent.db import DBSession, Base
from monitorrent.plugins import Topic
from monitorrent.plugins.status import Status
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, \
    TrackerPluginMixinBase, LoginResult, TrackerSettings
from tests import DbTestCase, TestCase


class MockTrackerPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    def _prepare_request(self, topic):
        if topic.url == 'http://mocktracker.com/1':
            return (topic.url, 'file.torrent'), None
        if topic.url == 'Russian 3 / English 3':
            raise Exception()
        return (topic.url, None), {}

    def parse_url(self, url):
        pass

    def can_parse_url(self, url):
        pass


class CreateEngineMixin(object):
    def create_engine_tracker(self):
        engine_downloads = MagicMock()
        engine_downloads.__enter__ = Mock(return_value=engine_downloads)
        engine_downloads.__exit__ = Mock(return_value=True)

        engine_topic = MagicMock()
        engine_topic.__enter__ = Mock(return_value=engine_topic)
        engine_topic.__exit__ = Mock(return_value=True)
        engine_topic.start = Mock(return_value=engine_downloads)

        engine_topics = MagicMock()
        engine_topics.__enter__ = Mock(return_value=engine_topics)
        engine_topics.__exit__ = Mock(return_value=True)
        engine_topics.start = Mock(return_value=engine_topic)

        engine_tracker = MagicMock()
        engine_tracker.__enter__ = Mock(return_value=engine_tracker)
        engine_tracker.__exit__ = Mock(return_value=True)
        engine_tracker.start = Mock(return_value=engine_topics)

        return engine_tracker, engine_topics, engine_topic, engine_downloads


class ExecuteWithHashChangeMixinTest(DbTestCase, CreateEngineMixin):
    class ExecuteMixinMockTopic(Topic):
        __tablename__ = "mocktopic_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'mocktracker.com'
        }

    def setUp(self):
        super(ExecuteWithHashChangeMixinTest, self).setUp()

        MockTrackerPlugin.topic_class = self.ExecuteMixinMockTopic
        Topic.metadata.create_all(self.engine)

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = br"d9:"
            if request[0] == 'http://mocktracker.com/3':
                raise Exception("Some strange exception")
            if request[0] == 'http://mocktracker.com/4':
                response.status_code = 500
                return response, None
            response.status_code = 200
            return response, request[1]

        last_update = datetime.now(pytz.utc)

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()
        engine_downloads.add_torrent.return_value = last_update

        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'HASH1'

        with DBSession() as db:
            topic1 = self.ExecuteMixinMockTopic(display_name='Russian / English',
                                                url='http://mocktracker.com/1',
                                                additional_attribute='English')
            topic2 = self.ExecuteMixinMockTopic(display_name='Russian 2 / English 2',
                                                url='http://mocktracker.com/2',
                                                additional_attribute='English 2',
                                                hash='HASH1')
            topic3 = self.ExecuteMixinMockTopic(display_name='Russian 3 / English 3',
                                                url='http://mocktracker.com/3',
                                                additional_attribute='English 3',
                                                hash='HASH2')
            topic4 = self.ExecuteMixinMockTopic(display_name='Russian 4 / English 4',
                                                url='http://mocktracker.com/4',
                                                additional_attribute='English 4',
                                                hash='HASH3')
            db.add(topic1)
            db.add(topic2)
            db.add(topic3)
            db.add(topic4)
            db.commit()
            topic1_id = topic1.id
            topic2_id = topic2.id
            topic3_id = topic3.id
            topic4_id = topic4.id
        plugin = MockTrackerPlugin()
        plugin.init(TrackerSettings(12, None))
        plugin.execute(plugin.get_topics(None), engine_tracker)
        with DBSession() as db:
            # was successfully updated
            topic = db.query(self.ExecuteMixinMockTopic).filter(self.ExecuteMixinMockTopic.id == topic1_id).first()
            self.assertEqual(topic.hash, torrent.info_hash)
            self.assertEqual(topic.last_update, last_update)
            self.assertEqual(topic.status, Status.Ok)

            # was not update updated because of not changed hash
            # so last_update wasn't changed as well and it was null
            topic = db.query(self.ExecuteMixinMockTopic).filter(self.ExecuteMixinMockTopic.id == topic2_id).first()
            self.assertEqual(topic.hash, torrent.info_hash)
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.Ok)

            # was not updated because of exception
            topic = db.query(self.ExecuteMixinMockTopic).filter(self.ExecuteMixinMockTopic.id == topic3_id).first()
            self.assertEqual(topic.hash, 'HASH2')
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.Ok)

            # was not updated because of status code
            topic = db.query(self.ExecuteMixinMockTopic).filter(self.ExecuteMixinMockTopic.id == topic4_id).first()
            self.assertEqual(topic.hash, 'HASH3')
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.Ok)


class ExecuteWithHashChangeMixinStatusTest(DbTestCase, CreateEngineMixin):
    class ExecuteMockTopic(Topic):
        __tablename__ = "mocktopic2_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'mocktracker2.com'
        }

    class MockTrackerPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
        def _prepare_request(self, topic):
            return (topic.url, 'file.torrent'), None

        def parse_url(self, url):
            pass

        def can_parse_url(self, url):
            pass

        def check_download(self, response):
            if response.status_code == 302 or response.status_code == 404:
                return Status.NotFound

            if response.status_code == 444:
                return Status.Unknown

            if response.status_code != 200:
                return Status.Error

            return Status.Ok

    def setUp(self):
        super(ExecuteWithHashChangeMixinStatusTest, self).setUp()

        self.MockTrackerPlugin.topic_class = self.ExecuteMockTopic
        Topic.metadata.create_all(self.engine)

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = br"d9:"
            if request[0] == 'http://mocktracker2.com/1':
                response.status_code = 302
                return response, None
            elif request[0] == 'http://mocktracker2.com/2':
                response.status_code = 500
                return response, None
            elif request[0] == 'http://mocktracker2.com/3':
                response.status_code = 444
                return response, None
            response.status_code = 200
            return response, request[1]

        last_update = datetime.now(pytz.utc)

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        engine_downloads.add_torrent.return_value = last_update

        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'HASH1'

        with DBSession() as db:
            topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                           url='http://mocktracker2.com/1',
                                           additional_attribute='English')
            topic2 = self.ExecuteMockTopic(display_name='Russian 2 / English 2',
                                           url='http://mocktracker2.com/2',
                                           additional_attribute='English 2',
                                           hash='OldHash1')
            topic3 = self.ExecuteMockTopic(display_name='Russian 3 / English 3',
                                           url='http://mocktracker2.com/3',
                                           additional_attribute='English 3',
                                           hash='OldHash2')
            topic4 = self.ExecuteMockTopic(display_name='Russian 4 / English 4',
                                           url='http://mocktracker2.com/4',
                                           additional_attribute='English 4',
                                           hash='OldHash3')
            db.add(topic1)
            db.add(topic2)
            db.add(topic3)
            db.add(topic4)
            db.commit()
            topic1_id = topic1.id
            topic2_id = topic2.id
            topic3_id = topic3.id
            topic4_id = topic4.id
            db.expunge_all()
        plugin = self.MockTrackerPlugin()
        plugin.init(TrackerSettings(12, None))
        plugin.execute(plugin.get_topics(None), engine_tracker)
        with DBSession() as db:
            # Status code 302 update status to NotFound
            topic = db.query(self.ExecuteMockTopic).filter(self.ExecuteMockTopic.id == topic1_id).first()
            self.assertIsNone(topic.hash)
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.NotFound)

            # Status code 500 update status to Error
            topic = db.query(self.ExecuteMockTopic).filter(self.ExecuteMockTopic.id == topic2_id).first()
            self.assertEqual(topic.hash, topic2.hash)
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.Error)

            # Status code 444 is Unknow status
            topic = db.query(self.ExecuteMockTopic).filter(self.ExecuteMockTopic.id == topic3_id).first()
            self.assertEqual(topic.hash, topic3.hash)
            self.assertIsNone(topic.last_update)
            self.assertEqual(topic.status, Status.Unknown)

            # Status code 200 is Ok status
            topic = db.query(self.ExecuteMockTopic).filter(self.ExecuteMockTopic.id == topic4_id).first()
            self.assertEqual(topic.hash, 'HASH1')
            self.assertEqual(topic.last_update, last_update)
            self.assertEqual(topic.status, Status.Ok)

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute_reset_status_and_download(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = br"d9:"
            response.status_code = 200
            return response, request[1]

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        last_update = datetime.now(pytz.utc)
        engine_downloads.add_torrent.return_value = last_update
        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'HASH1'

        with DBSession() as db:
            topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                           url='http://mocktracker2.com/1',
                                           additional_attribute='English',
                                           hash='OLDHASH',
                                           status=Status.Error)
            db.add(topic1)
            db.commit()
            topic1_id = topic1.id
            db.expunge_all()
        plugin = self.MockTrackerPlugin()
        plugin.init(TrackerSettings(12, None))
        plugin.execute(plugin.get_topics(None), engine_tracker)
        with DBSession() as db:
            topic = db.query(self.ExecuteMockTopic).filter(self.ExecuteMockTopic.id == topic1_id).first()
            self.assertEqual(topic.last_update, last_update)
            self.assertEqual(topic.status, Status.Ok)
            self.assertEqual(topic.hash, 'HASH1')

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute_check_changes_true_should_download_torrent(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = br"d9:"
            response.status_code = 200
            return response, request[1]

        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'HASH1'

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                       url='http://mocktracker2.com/1',
                                       additional_attribute='English',
                                       hash='OLDHASH',
                                       status=Status.Error)
        plugin = self.MockTrackerPlugin()
        plugin.check_changes = Mock(return_value=True)
        plugin.init(TrackerSettings(12, None))
        plugin.execute([topic1], engine_tracker)

        plugin.check_changes.assert_called_once_with(topic1)
        download.assert_called_once_with(('http://mocktracker2.com/1', 'file.torrent'), proxies=ANY, timeout=ANY)

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute_check_changes_true_and_not_changes_hash_should_call_save_topic(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = six.text_type("d9:")
            response.status_code = 200
            return response, request[1]

        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'OLDHASH'

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                       url='http://mocktracker2.com/1',
                                       additional_attribute='English',
                                       hash='OLDHASH',
                                       status=Status.Ok)
        plugin = self.MockTrackerPlugin()
        plugin.check_changes = Mock(return_value=True)
        plugin.init(TrackerSettings(12, None))
        plugin.save_topic = Mock()
        plugin.execute([topic1], engine_tracker)

        plugin.check_changes.assert_called_once_with(topic1)
        download.assert_called_once_with(('http://mocktracker2.com/1', 'file.torrent'), proxies=ANY, timeout=ANY)
        plugin.save_topic.assert_called_once_with(topic1, None, Status.Ok)

    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute_check_changes_false_should_stop_download_torrent(self, download):

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                       url='http://mocktracker2.com/1',
                                       additional_attribute='English',
                                       hash='OLDHASH',
                                       status=Status.Error)
        plugin = self.MockTrackerPlugin()
        plugin.check_changes = Mock(return_value=False)
        plugin.init(TrackerSettings(12, None))
        plugin.execute([topic1], engine_tracker)

        plugin.check_changes.assert_called_once_with(topic1)
        download.assert_not_called()

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    def test_execute_and_download_html_should_failed(self, download, torrent_mock):
        def download_func(request, **kwargs):
            self.assertEqual(12, kwargs['timeout'])
            response = Response()
            response._content = "<html>HTML</html>"
            response.status_code = 200
            response.headers['content-type'] = 'text/html'
            return response, request[1]

        download.side_effect = download_func
        torrent = torrent_mock.return_value
        torrent.info_hash = 'OLDHASH'

        engine_tracker, _, _, engine_downloads = self.create_engine_tracker()

        topic1 = self.ExecuteMockTopic(display_name='Russian / English',
                                       url='http://mocktracker2.com/1',
                                       additional_attribute='English',
                                       hash='OLDHASH',
                                       status=Status.Ok)
        plugin = self.MockTrackerPlugin()
        plugin.check_changes = Mock(return_value=True)
        plugin.init(TrackerSettings(12, None))
        plugin.save_topic = Mock()
        plugin.execute([topic1], engine_tracker)

        plugin.check_changes.assert_called_once_with(topic1)
        download.assert_called_once_with(('http://mocktracker2.com/1', 'file.torrent'), proxies=ANY, timeout=ANY)
        engine_tracker.failed.assert_called_once()
        plugin.save_topic.assert_not_called()

@ddt
class TrackerPluginBaseTest(DbTestCase):
    class MockTopic(Topic):
        __tablename__ = "mocktopic_base_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'base.mocktracker.com'
        }

    class WrongMockTopic(Topic):
        __tablename__ = "wrong_mocktopic_base_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'wrong.base.mocktracker.com'
        }

    def setUp(self):
        super(TrackerPluginBaseTest, self).setUp()

        MockTrackerPlugin.topic_class = self.MockTopic
        Topic.metadata.create_all(self.engine)

    def test_prepare_add_topic(self):
        plugin = MockTrackerPlugin()
        plugin.parse_url = Mock(return_value={'original_name': 'Torrent 1'})
        result = plugin.prepare_add_topic('http://mocktracker.com/torrent/1')

        self.assertEqual({'display_name': 'Torrent 1'}, result)

    def test_prepare_add_topic_fail(self):
        plugin = MockTrackerPlugin()
        plugin.parse_url = Mock(return_value=None)
        result = plugin.prepare_add_topic('http://mocktracker.com/torrent/1')

        self.assertIsNone(result)

    def test_add_topic(self):
        plugin = MockTrackerPlugin()
        plugin.parse_url = Mock(return_value={'original_name': 'Torrent 1'})
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        url = 'http://mocktracker.com/torrent/1'
        params = {
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text'
        }

        self.assertTrue(plugin.add_topic(url, params))

        with DBSession() as db:
            topic = db.query(self.MockTopic).first()

            self.assertIsNotNone(topic)
            self.assertEqual(topic.url, url)
            self.assertEqual(topic.display_name, params['display_name'])
            self.assertEqual(topic.additional_attribute, params['additional_attribute'])
            self.assertEqual(topic.type, 'base.mocktracker.com')

    def test_add_topic_fail(self):
        plugin = MockTrackerPlugin()
        plugin.parse_url = Mock(return_value=None)
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        url = 'http://mocktracker.com/torrent/1'
        params = {
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text'
        }

        self.assertFalse(plugin.add_topic(url, params))

    def test_get_topic(self):
        plugin = MockTrackerPlugin()
        plugin.topic_class = self.MockTopic
        fields = {
            'url': u'http://base.mocktracker.org/torrent/1',
            'display_name': u'Original Name / Translated Name / Info',
            'additional_attribute': u'Text',
            'type': 'base.mocktracker.com',
        }
        with DBSession() as db:
            topic = self.MockTopic(**fields)
            db.add(topic)
            db.commit()
            fields['id'] = topic.id

        result = plugin.get_topic(fields['id'])
        expected = {
            'id': fields['id'],
            'display_name': fields['display_name'],
            'url': fields['url'],
            'last_update': None,
            'info': None,
            'status': Status.Ok,
            'download_dir': None
        }
        self.assertEqual(expected, result)

        # noinspection PyTypeChecker
        self.assertIsNone(plugin.get_topic(fields['id'] + 1))

    @unpack
    @data({'last_update': datetime(2016, 3, 15, 18, 58, 12, tzinfo=pytz.utc), 'status': Status.Ok},
          {'last_update': None, 'status': Status.Error})
    def test_save_topic(self, last_update, status):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        original_url = 'http://base.mocktracker.org/torrent/1'
        topic_last_update = datetime(2016, 3, 14, 18, 58, 12, tzinfo=pytz.utc)
        fields = {
            'url': original_url,
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text',
            'type': 'base.mocktracker.com',
            'status': Status.Ok,
            'last_update': topic_last_update
        }
        with DBSession() as db:
            topic = self.MockTopic(**fields)
            db.add(topic)
            db.commit()
            fields['id'] = topic.id

        topic = plugin.get_topics(None)[0]
        plugin.save_topic(topic, last_update, status)

        topic = plugin.get_topics(None)[0]
        self.assertEqual(last_update or topic_last_update, topic.last_update)
        self.assertEqual(status, topic.status)

    def test_save_topic_failed(self):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        original_url = 'http://base.mocktracker.org/torrent/1'
        topic_last_update = datetime(2016, 3, 14, 18, 58, 12, tzinfo=pytz.utc)
        fields = {
            'url': original_url,
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text',
            'type': 'base.mocktracker.com',
            'status': Status.Ok,
            'last_update': topic_last_update
        }

        with self.assertRaises(Exception):
            topic = self.WrongMockTopic(**fields)
            plugin.save_topic(topic, None, Status.Ok)

    def test_update_topic(self):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        original_url = 'http://base.mocktracker.org/torrent/1'
        fields = {
            'url': original_url,
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text',
            'type': 'base.mocktracker.com',
        }
        with DBSession() as db:
            topic = self.MockTopic(**fields)
            db.add(topic)
            db.commit()
            fields['id'] = topic.id

        # url shouldn't be updated
        fields['url'] = u'http://base.mocktracker.org/torrent/2'
        fields['display_name'] = u'Original Name / Translated Name / Info 2'
        fields['additional_attribute'] = 'Text 2'

        self.assertTrue(plugin.update_topic(fields['id'], fields))
        expected = {
            'id': fields['id'],
            'display_name': fields['display_name'],
            'url': original_url,
            'last_update': None,
            'info': None,
            'status': Status.Ok,
            'download_dir': None
        }
        self.assertEqual(expected, plugin.get_topic(fields['id']))

        # noinspection PyTypeChecker
        self.assertFalse(plugin.update_topic(fields['id'] + 1, fields))

    def test_get_topics_by_id(self):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        all_topics = []
        for i in range(1, 10):
            with DBSession() as db:
                topic_fields = {
                    'url': 'http://base.mocktracker.org/torrent/{0}'.format(i),
                    'display_name': 'Original Name / Translated Name / Info {0}'.format(i),
                    'additional_attribute': 'Text {0}'.format(i),
                    'type': 'base.mocktracker.com',
                }
                new_topic = self.MockTopic(**topic_fields)

                db.add(new_topic)
                db.commit()
                topic_fields['id'] = new_topic.id

                all_topics.append(topic_fields)

        # get all topics
        topics = plugin.get_topics(None)
        self.assertEqual(len(topics), len(all_topics))

        # get first half of topics
        half_topics = all_topics[:int(len(all_topics) / 2)]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        self.assertEqual(len(topics), len(half_topics))

        # get second half of topics
        half_topics = all_topics[int(len(all_topics) / 2):]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        self.assertEqual(len(topics), len(half_topics))

    def test_get_topics_filter_by_status(self):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        all_topics = []
        for i in range(1, 10):
            with DBSession() as db:
                topic_fields = {
                    'url': 'http://base.mocktracker.org/torrent/{0}'.format(i),
                    'display_name': 'Original Name / Translated Name / Info {0}'.format(i),
                    'additional_attribute': 'Text {0}'.format(i),
                    'type': 'base.mocktracker.com',
                    'status': Status.Ok if i % 3 == 0 else Status.Error if i % 3 == 1 else Status.NotFound
                }
                new_topic = self.MockTopic(**topic_fields)

                db.add(new_topic)
                db.commit()
                topic_fields['id'] = new_topic.id

                all_topics.append(topic_fields)

        # get all topics
        # by default we rerun execute only for Ok and Error topics
        # all other statuses will be skipped
        ok_and_error_topics = list(filter(lambda topic: topic['status'] in [Status.Ok, Status.Error], all_topics))
        topics = plugin.get_topics(None)
        self.assertEqual(len(topics), len(ok_and_error_topics))

        # but when we specify ids we will return all topics regardless to topic status
        topics = plugin.get_topics([t['id'] for t in all_topics])
        self.assertEqual(len(topics), len(all_topics))

        # get first half of topics
        half_topics = all_topics[:int(len(all_topics) / 2)]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        self.assertEqual(len(topics), len(half_topics))

        # get second half of topics
        half_topics = all_topics[int(len(all_topics) / 2):]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        self.assertEqual(len(topics), len(half_topics))

    def test_get_topics_filter_by_pause_state(self):
        plugin = MockTrackerPlugin()
        plugin.topic_private_fields = plugin.topic_private_fields + ['additional_attribute']
        plugin.topic_class = self.MockTopic
        all_topics = []
        for i in range(1, 10):
            with DBSession() as db:
                topic_fields = {
                    'url': 'http://base.mocktracker.org/torrent/{0}'.format(i),
                    'display_name': 'Original Name / Translated Name / Info {0}'.format(i),
                    'additional_attribute': 'Text {0}'.format(i),
                    'type': 'base.mocktracker.com',
                    'status': Status.Ok if i % 3 == 0 else Status.Error if i % 3 == 1 else Status.NotFound,
                    'paused': i > 8
                }
                new_topic = self.MockTopic(**topic_fields)

                db.add(new_topic)
                db.commit()
                topic_fields['id'] = new_topic.id

                all_topics.append(topic_fields)

        # get all topics
        # by default we rerun execute only for Ok and Error topics
        # all other statuses will be skipped
        ok_and_error_topics = [t for t in all_topics if t['status'] in [Status.Ok, Status.Error]]
        ok_and_error_not_paused = [t for t in ok_and_error_topics if not t['paused']]
        self.assertNotEqual(len(ok_and_error_topics), len(ok_and_error_not_paused))
        topics = plugin.get_topics(None)
        self.assertEqual(len(topics), len(ok_and_error_not_paused))

        # but when we specify ids we will return all topics regardless to topic status
        all_not_paused = [t for t in all_topics if not t['paused']]
        topics = plugin.get_topics([t['id'] for t in all_topics])
        self.assertEqual(len(topics), len(all_not_paused))

        # get first half of topics
        half_topics = all_topics[:int(len(all_topics) / 2)]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        self.assertEqual(len(topics), len(half_topics))

        # get second half of topics
        half_topics = all_topics[int(len(all_topics) / 2):]
        topics = plugin.get_topics([t['id'] for t in half_topics])
        half_not_paused = [t for t in half_topics if not t['paused']]
        self.assertEqual(len(topics), len(half_not_paused))


class TrackerPluginMixinTest(TestCase):
    class MockTopic2(Topic):
        __tablename__ = "mocktopic_mixin_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'mixin.mocktracker.com'
        }

    def test_base_mixin_right_inheritance(self):
        empty_lambda = lambda *a, **d: None
        plugin_type = type('MockTrackerPlugin2', (TrackerPluginMixinBase, TrackerPluginBase),
                           {
                               '_prepare_request': empty_lambda,
                               'parse_url': empty_lambda,
                               'can_parse_url': empty_lambda,
                               'execute': empty_lambda
                           })
        plugin_type()

    def test_base_mixin_wrong_inheritance(self):
        plugin_type = type('MockTrackerPlugin2', (TrackerPluginMixinBase, ), {})
        with self.assertRaises(Exception) as e:
            plugin_type()
        self.assertEqual(str(e.exception),
                         'TrackerPluginMixinBase can be applied only to TrackerPluginBase classes')

    def test_execute_mixin_right_inheritance(self):
        empty_lambda = lambda *a, **d: None
        plugin_type = type('MockTrackerPlugin2', (ExecuteWithHashChangeMixin, TrackerPluginBase),
                           {
                               '_prepare_request': empty_lambda,
                               'parse_url': empty_lambda,
                               'can_parse_url': empty_lambda,
                           })
        plugin_type.topic_class = self.MockTopic2
        plugin_type()

    def test_execute_mixin_wrong_inheritance(self):
        empty_lambda = lambda *a, **d: None
        plugin_type = type('MockTrackerPlugin2', (ExecuteWithHashChangeMixin, TrackerPluginBase),
                           {
                               '_prepare_request': empty_lambda,
                               'parse_url': empty_lambda,
                               'can_parse_url': empty_lambda,
                           })
        with self.assertRaises(Exception) as e:
            plugin_type()
        self.assertEqual(str(e.exception),
                         "ExecuteWithHashMixin can be applied only to TrackerPluginBase class "
                         "with hash attribute in topic_class")


class LoginResultStrTest(TestCase):
    def test_str(self):
        self.assertEqual(str(LoginResult.Ok), 'Ok')
        self.assertEqual(str(LoginResult.CredentialsNotSpecified), "Credentials not specified")
        self.assertEqual(str(LoginResult.IncorrentLoginPassword), "Incorrent login/password")
        self.assertEqual(str(LoginResult.InternalServerError), "Internal server error")
        self.assertEqual(str(LoginResult.ServiceUnavailable), "Service unavailable")
        self.assertEqual(str(LoginResult.Unknown), "Unknown")


@ddt
class WithCredentialsMixinTest(DbTestCase):
    class MockCredentials(Base):
        __tablename__ = "mock_credentials"

        username = Column(String, primary_key=True)
        password = Column(String, primary_key=True)

    empty_lambda = lambda *a, **d: None
    plugin_type = type('MockPlugin2', (WithCredentialsMixin, TrackerPluginBase),
                       {
                           '_prepare_request': empty_lambda,
                           'parse_url': empty_lambda,
                           'can_parse_url': empty_lambda,
                           'login': lambda s: LoginResult.Ok,
                           'verify': lambda s: True,
                           'credentials_class': MockCredentials
                       })

    def test_credentials(self):
        plugin = self.plugin_type()

        self.assertIsNone(plugin.get_credentials())

        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})

        self.assertEqual({'username': 'monitorrent'}, plugin.get_credentials())

    @unpack
    @data({'verify_result': True, 'login_result': LoginResult.Ok, 'expected': True},
          {'verify_result': False, 'login_result': LoginResult.Ok, 'expected': True},
          {'verify_result': False, 'login_result': LoginResult.CredentialsNotSpecified, 'expected': False},
          {'verify_result': False, 'login_result': LoginResult.IncorrentLoginPassword, 'expected': False},)
    def test_execute_login(self, verify_result, login_result, expected):
        plugin_type2 = type('MockPlugin3', (self.plugin_type, ),
                            {
                                'verify': lambda s: verify_result,
                                'login': lambda s: login_result,
                            })
        plugin = plugin_type2()
        engine = Mock()
        # noinspection PyProtectedMember
        self.assertEqual(expected, plugin._execute_login(engine))

    @data(True, False)
    def test_execute(self, value):
        execute_mock = Mock()
        plugin_type2 = type('ExecuteMixin', (TrackerPluginMixinBase, ),
                            {
                                'execute': execute_mock,
                            })
        plugin_type3 = type('MockPlugin4', (WithCredentialsMixin, plugin_type2, TrackerPluginBase, ),
                            {
                                '_prepare_request': self.empty_lambda,
                                'parse_url': self.empty_lambda,
                                'can_parse_url': self.empty_lambda,
                                'verify': lambda s: value,
                                'login': lambda s: LoginResult.IncorrentLoginPassword
                            })
        plugin = plugin_type3()

        engine = Mock()
        plugin.execute(None, engine)
        if value:
            execute_mock.assert_called_with(None, engine)
        else:
            execute_mock.assert_not_called()
