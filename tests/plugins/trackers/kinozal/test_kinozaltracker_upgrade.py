import pytz
from monitorrent.plugins.trackers.kinozal import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from datetime import datetime
from monitorrent.db import UTCDateTime
from tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class KinozalTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    KinozalTopic0 = Table("Kinozal_topics", m0,
                          Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                          Column("hash", String, nullable=True))
    KinozalCredentials0 = Table("Kinozal_credentials", m0,
                                Column('username', String, primary_key=True),
                                Column('password', String, primary_key=True),
                                Column('c_uid', String, nullable=True),
                                Column('c_pass', String, nullable=True))

    m1 = MetaData()
    KinozalTopic1 = Table("kinozal_topics", m1,
                          Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                          Column("hash", String, nullable=True),
                          Column("last_torrent_update", UTCDateTime, nullable=True))

    KinozalCredentials1 = Table("kinozal_credentials", m1,
                                Column('username', String, primary_key=True),
                                Column('password', String, primary_key=True),
                                Column('c_uid', String, nullable=True),
                                Column('c_pass', String, nullable=True))

    versions = [
        (KinozalTopic0, UpgradeTestCase.copy(Topic.__table__, m0), KinozalCredentials0),
        (KinozalTopic1, UpgradeTestCase.copy(Topic.__table__, m1), KinozalCredentials1),
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
        topic = {'id': 1, 'url': 'http://1', 'display_name': '1', 'type': 'kinozal.tv'}
        kinozal_topic = {'id':1, 'hash': 'a1b'}
        credentials = {'username': 'username', 'password': 'password', 'c_uid': '123456', 'c_pass': 'pass'}

        self._upgrade_from([[kinozal_topic], [topic], [credentials]], 0)

