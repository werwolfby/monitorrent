from monitorrent.plugins.trackers.rutor import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from datetime import datetime
from monitorrent.db import UTCDateTime
from monitorrent.tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class RutorTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    RutorOrgTopic0 = Table("rutororg_topics", m0,
                           Column('id', Integer, primary_key=True),
                           Column('name', String, unique=True, nullable=False),
                           Column('url', String, nullable=False, unique=True),
                           Column('hash', String, nullable=False),
                           Column('last_update', UTCDateTime, nullable=True))

    m1 = MetaData()
    TopicsLast1 = UpgradeTestCase.copy(Topic.__table__, m1)
    RutorOrgTopic1 = Table('rutororg_topics', m1,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=False))

    m2 = MetaData()
    TopicsLast2 = UpgradeTestCase.copy(Topic.__table__, m2)
    RutorOrgTopic2 = Table('rutororg_topics', m2,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=True))
    versions = [
        (RutorOrgTopic0, ),
        (RutorOrgTopic1, ),
        (RutorOrgTopic2, ),
    ]

    def upgrade_func(self, engine, operation_factory):
        upgrade(engine, operation_factory)

    def _get_current_version(self):
        return get_current_version(self.engine)

    def test_empty_db_test(self):
        self._test_empty_db_test()

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    def test_updage_filled_from_version_0(self):
        topic1 = {'url': 'http://1', 'name': '1', 'hash': 'a1b'}
        topic2 = {'url': 'http://2', 'name': '2', 'hash': 'a1b'}
        topic3 = {'url': 'http://5', 'name': '5', 'hash': 'a1b', 'last_update': datetime.now()}

        self._upgrade_from([[topic1, topic2, topic3]], 0)

