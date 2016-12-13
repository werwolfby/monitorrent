import pytz
from monitorrent.db import UTCDateTime
from monitorrent.plugins import Status, upgrade, get_current_version
from sqlalchemy import Column, Integer, String, Boolean, MetaData, Table
from sqlalchemy_enum34 import EnumType
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from datetime import datetime
from tests import UpgradeTestCase


class TopicUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    Topic0 = Table("topics", m0,
                   Column('id', Integer, primary_key=True),
                   Column('display_name', String, unique=True, nullable=False),
                   Column('url', String, nullable=False, unique=True),
                   Column('last_update', UTCDateTime, nullable=True),
                   Column('type', String))
    m1 = MetaData()
    Topic1 = Table("topics", m1,
                   Column('id', Integer, primary_key=True),
                   Column('display_name', String, unique=True, nullable=False),
                   Column('url', String, nullable=False, unique=True),
                   Column('last_update', UTCDateTime, nullable=True),
                   Column('type', String),
                   Column('status', EnumType(Status, by_name=True), nullable=False, server_default=Status.Ok.__str__()))
    m2 = MetaData()
    Topic2 = Table("topics", m2,
                   Column('id', Integer, primary_key=True),
                   Column('display_name', String, unique=True, nullable=False),
                   Column('url', String, nullable=False, unique=True),
                   Column('last_update', UTCDateTime, nullable=True),
                   Column('type', String),
                   Column('status', EnumType(Status, by_name=True), nullable=False, server_default=Status.Ok.__str__()),
                   Column('paused', Boolean, nullable=False, server_default='0'))
    m3 = MetaData()
    Topic3 = Table("topics", m3,
                   Column('id', Integer, primary_key=True),
                   Column('display_name', String, unique=True, nullable=False),
                   Column('url', String, nullable=False, unique=True),
                   Column('last_update', UTCDateTime, nullable=True),
                   Column('type', String),
                   Column('status', EnumType(Status, by_name=True), nullable=False, server_default=Status.Ok.__str__()),
                   Column('paused', Boolean, nullable=False, server_default='0'),
                   Column('download_dir', String, nullable=True, server_default=None))
    versions = [
        (Topic0, ),
        (Topic1, ),
        (Topic2, ),
        (Topic3, )
    ]

    def upgrade_func(self, engine, operation_factory):
        upgrade(engine, operation_factory)

    def _get_current_version(self):
        return get_current_version(self.engine)

    def test_empty_db_test(self):
        self._test_empty_db_test()

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    def test_updage_empty_from_version_1(self):
        self._upgrade_from(None, 1)

    def test_updage_empty_from_version_2(self):
        self._upgrade_from(None, 2)

    def test_updage_empty_from_version_3(self):
        self._upgrade_from(None, 3)

    def test_updage_filled_from_version_0(self):
        topic1 = {'url': 'http://1', 'display_name': '1'}
        topic2 = {'url': 'http://2', 'display_name': '2'}
        topic3 = {'url': 'http://3', 'display_name': '3'}
        topic4 = {'url': 'http://4', 'display_name': '4'}
        topic5 = {'url': 'http://5', 'display_name': '5', 'last_update': datetime.now(pytz.utc)}

        self._upgrade_from([[topic1, topic2, topic3, topic4, topic5]], 0)

        session_factory = sessionmaker(class_=Session, bind=self.engine)
        session = scoped_session(session_factory)

        db = session()
        try:
            topics = db.query(self.versions[-1][0]).all()

            for topic in topics:
                self.assertEqual(topic.status, Status.Ok)
                self.assertEqual(topic.paused, False)
                self.assertIsNone(topic.download_dir)
        finally:
            db.close()



