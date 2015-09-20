from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey
from ddt import ddt, data, unpack
from mock import patch, Mock
from monitorrent.db import DBSession, Base
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, \
    TrackerPluginMixinBase, LoginResult
from monitorrent.tests import DbTestCase, TestCase


class MockTrackerPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    def _prepare_request(self, topic):
        if topic.display_name == 'Russian / English':
            return topic.display_name, 'file.torrent'
        if topic.display_name == 'Russian 3 / English 3':
            raise Exception()
        return topic.display_name, None

    def parse_url(self, url):
        pass

    def can_parse_url(self, url):
        pass


class ExecuteWithHashChangeMixinTest(DbTestCase):
    class MockTopic(Topic):
        __tablename__ = "mocktopic_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'mocktracker.com'
        }

    def setUp(self):
        super(ExecuteWithHashChangeMixinTest, self).setUp()

        MockTrackerPlugin.topic_class = self.MockTopic
        Topic.metadata.create_all(self.engine)

    @patch('monitorrent.plugins.trackers.Torrent', create=True)
    @patch('monitorrent.plugins.trackers.download', create=True)
    @patch('monitorrent.engine.Engine')
    def test_execute(self, engine, download, torrent_mock):
        last_update = datetime.now()
        engine.add_torrent.return_value = last_update
        download.side_effect = lambda v: v
        torrent = torrent_mock.return_value
        torrent.info_hash = 'HASH1'

        with DBSession() as db:
            topic1 = self.MockTopic(display_name='Russian / English',
                                    url='http://mocktracker.com/1',
                                    additional_attribute='English')
            topic2 = self.MockTopic(display_name='Russian 2 / English 2',
                                    url='http://mocktracker.com/2',
                                    additional_attribute='English 2',
                                    hash='HASH1')
            topic3 = self.MockTopic(display_name='Russian 3 / English 3',
                                    url='http://mocktracker.com/3',
                                    additional_attribute='English 3',
                                    hash='HASH2')
            db.add(topic1)
            db.add(topic2)
            db.add(topic3)
            db.commit()
            topic1_id = topic1.id
            topic2_id = topic2.id
            topic3_id = topic3.id
        plugin = MockTrackerPlugin()
        plugin.execute(None, engine)
        with DBSession() as db:
            topic = db.query(self.MockTopic).filter(self.MockTopic.id == topic1_id).first()
            self.assertEqual(topic.hash, torrent.info_hash)
            self.assertEqual(topic.last_update, last_update)

            topic = db.query(self.MockTopic).filter(self.MockTopic.id == topic2_id).first()
            self.assertEqual(topic.hash, torrent.info_hash)
            self.assertIsNone(topic.last_update)

            topic = db.query(self.MockTopic).filter(self.MockTopic.id == topic3_id).first()
            self.assertEqual(topic.hash, 'HASH2')
            self.assertIsNone(topic.last_update)


class TrackerPluginBaseTest(DbTestCase):
    class MockTopic(Topic):
        __tablename__ = "mocktopic_base_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'base.mocktracker.com'
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
            'url': 'http://base.mocktracker.org/torrent/1',
            'display_name': 'Original Name / Translated Name / Info',
            'additional_attribute': 'Text',
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
        }
        self.assertEqual(expected, result)

        # noinspection PyTypeChecker
        self.assertIsNone(plugin.get_topic(fields['id'] + 1))

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
        fields['url'] = 'http://base.mocktracker.org/torrent/2'
        fields['display_name'] = 'Original Name / Translated Name / Info 2'
        fields['additional_attribute'] = 'Text 2'

        self.assertTrue(plugin.update_topic(fields['id'], fields))
        expected = {
            'id': fields['id'],
            'display_name': fields['display_name'],
            'url': original_url,
            'last_update': None,
            'info': None,
        }
        self.assertEqual(expected, plugin.get_topic(fields['id']))

        # noinspection PyTypeChecker
        self.assertFalse(plugin.update_topic(fields['id'] + 1, fields))


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
        self.assertEqual(e.exception.message,
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
        self.assertEqual(e.exception.message,
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

