from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from mock import MagicMock, patch, PropertyMock
from monitorrent.db import DBSession
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase
from monitorrent.tests import DbTestCase


class MockTrackerPlugin(TrackerPluginBase):
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


class TrackerPluginBaseTest(DbTestCase):
    class MockTopic(Topic):
        __tablename__ = "mocktopic_series"

        id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
        additional_attribute = Column(String, nullable=False)
        hash = Column(String, nullable=True)

        __mapper_args__ = {
            'polymorphic_identity': 'mocktracker.com'
        }

    def setUp(self):
        super(TrackerPluginBaseTest, self).setUp()

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
