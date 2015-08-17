from monitorrent.plugins.trackers.rutor import upgrade
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from datetime import datetime
from monitorrent.tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class RutorTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    RutorOrgTopic0 = Table("rutororg_topics", m0,
                           Column('id', Integer, primary_key=True),
                           Column('name', String, unique=True, nullable=False),
                           Column('url', String, nullable=False, unique=True),
                           Column('hash', String, nullable=False),
                           Column('last_update', DateTime, nullable=True))

    m1 = MetaData()
    TopicsLast = UpgradeTestCase.copy(Topic.__table__, m1)
    RutorOrgTopic1 = Table('rutororg_topics', m1,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=False))
    versions = [
        (RutorOrgTopic0, ),
        (RutorOrgTopic1, )
    ]

    def _upgrade(self):
        return upgrade(self.engine, self.operation_factory)

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    def test_updage_filled_from_version_0(self):
        topic1 = {'url': 'http://1', 'name': '1', 'hash': 'a1b'}
        topic2 = {'url': 'http://2', 'name': '2', 'hash': 'a1b'}
        topic3 = {'url': 'http://5', 'name': '5', 'hash': 'a1b', 'last_update': datetime.now()}

        self._upgrade_from([[topic1, topic2, topic3]], 0)
