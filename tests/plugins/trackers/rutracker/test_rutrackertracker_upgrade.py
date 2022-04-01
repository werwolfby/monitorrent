# coding=utf-8
from monitorrent.settings_manager import Settings, ProxySettings
from monitorrent.plugins.trackers.rutracker import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class RuTrackerTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    Topic0 = UpgradeTestCase.copy(Topic.__table__, m0)
    RutrackerTopic0 = Table("rutracker_topics", m0,
                            Column('id', Integer, ForeignKey('topics.id'), primary_key=True),
                            Column('hash', String, nullable=True))
    RutrackerCredentials0 = Table("rutracker_credentials", m0,
                                  Column('username', String, primary_key=True),
                                  Column('password', String, primary_key=True),
                                  Column("uid", String, nullable=True),
                                  Column("bb_data", String, nullable=True))

    m1 = MetaData()
    Topic1 = UpgradeTestCase.copy(Topic.__table__, m1)
    RutrackerTopic1 = UpgradeTestCase.copy(RutrackerTopic0, m1)
    RutrackerCredentials1 = Table("rutracker_credentials", m1,
                                  Column('username', String, primary_key=True),
                                  Column('password', String, primary_key=True),
                                  Column("uid", String, nullable=True),
                                  Column("bb_data", String, nullable=True),
                                  Column("cookies", String, nullable=True),
                                  Column("headers", String, nullable=True))

    versions = [
        (Topic0, RutrackerTopic0, RutrackerCredentials0),
        (Topic1, RutrackerTopic1, RutrackerCredentials1),
    ]

    @classmethod
    def setUpClass(cls):
        for version in cls.versions:
            metadata = version[0].metadata

            # this tables required for latest upgrade
            cls.copy(ProxySettings.__table__, metadata)
            cls.copy(Settings.__table__, metadata)

    def upgrade_func(self, engine, operation_factory):
        upgrade(engine, operation_factory)

    def _get_current_version(self):
        return get_current_version(self.engine)

    def test_empty_db_test(self):
        self._test_empty_db_test()

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)
