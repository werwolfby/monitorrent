import pytz
from monitorrent.db import UTCDateTime
from monitorrent.plugins.trackers.lostfilm import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from datetime import datetime
from tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class LostFilmTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    LostFilmTVSeries0 = Table("lostfilmtv_series", m0,
                              Column('id', Integer, primary_key=True),
                              Column('display_name', String, unique=True, nullable=False),
                              Column('search_name', String, nullable=False),
                              Column('url', String, nullable=False, unique=True),
                              Column('season_number', Integer, nullable=True),
                              Column('episode_number', Integer, nullable=True),
                              Column('last_update', UTCDateTime, nullable=True))
    LostFilmTVCredentials0 = Table("lostfilmtv_credentials", m0,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('uid', String),
                                   Column('pass', String),
                                   Column('usess', String))
    m1 = MetaData()
    LostFilmTVSeries1 = Table("lostfilmtv_series", m1,
                              Column('id', Integer, primary_key=True),
                              Column('display_name', String, unique=True, nullable=False),
                              Column('search_name', String, nullable=False),
                              Column('url', String, nullable=False, unique=True),
                              Column('season_number', Integer, nullable=True),
                              Column('episode_number', Integer, nullable=True),
                              Column('last_update', UTCDateTime, nullable=True),
                              Column('quality', String, nullable=False, server_default='SD'))
    LostFilmTVCredentials1 = Table("lostfilmtv_credentials", m1,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('uid', String),
                                   Column('pass', String),
                                   Column('usess', String))
    m2 = MetaData()
    LostFilmTVSeries2 = Table("lostfilmtv_series", m2,
                              Column('id', Integer, ForeignKey('topics.id'), primary_key=True),
                              Column('search_name', String, nullable=False),
                              Column('season', Integer, nullable=True),
                              Column('episode', Integer, nullable=True),
                              Column('quality', String, nullable=False, server_default='SD'))
    LostFilmTVCredentials2 = UpgradeTestCase.copy(LostFilmTVCredentials1, m2)
    m3 = MetaData()
    LostFilmTVSeries3 = UpgradeTestCase.copy(LostFilmTVSeries2, m3)
    LostFilmTVCredentials3 = Table("lostfilmtv_credentials", m3,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('uid', String),
                                   Column('pass', String),
                                   Column('usess', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))

    versions = [
        (LostFilmTVSeries0, LostFilmTVCredentials0),
        (LostFilmTVSeries1, LostFilmTVCredentials1),
        (LostFilmTVSeries2, UpgradeTestCase.copy(Topic.__table__, m2), LostFilmTVCredentials2),
        (LostFilmTVSeries3, LostFilmTVCredentials3),
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

    def test_updage_filled_from_version_0(self):
        topic1 = {'url': 'http://1', 'display_name': '1', 'search_name': '1'}
        topic2 = {'url': 'http://2', 'display_name': '2', 'search_name': '2'}
        topic3 = {'url': 'http://3', 'display_name': '3', 'search_name': '3', 'season_number': 1}
        topic4 = {'url': 'http://4', 'display_name': '4', 'search_name': '4', 'season_number': 1, 'episode_number': 1}
        topic5 = {'url': 'http://5', 'display_name': '5', 'search_name': '5', 'season_number': 1, 'episode_number': 1, 'last_update': datetime.now(pytz.utc)}

        self._upgrade_from([[topic1, topic2, topic3, topic4, topic5]], 0)

    def test_updage_filled_from_version_1(self):
        topic1 = {'url': 'http://1', 'display_name': '1', 'search_name': '1', 'quality': 'SD'}
        topic2 = {'url': 'http://2', 'display_name': '2', 'search_name': '2', 'quality': '720p'}
        topic3 = {'url': 'http://3', 'display_name': '3', 'search_name': '3', 'season_number': 1, 'quality': '1080p'}
        topic4 = {'url': 'http://4', 'display_name': '4', 'search_name': '4', 'season_number': 1, 'episode_number': 1, 'quality': 'SD'}
        topic5 = {'url': 'http://5', 'display_name': '5', 'search_name': '5', 'season_number': 1, 'episode_number': 1, 'quality': '720p', 'last_update': datetime.now(pytz.utc)}

        self._upgrade_from([[topic1, topic2, topic3, topic4, topic5]], 1)

    def test_updage_filled_from_version_2(self):
        topic1 = {'id': 1, 'url': 'http://1', 'display_name': '1', 'search_name': '1', 'quality': 'SD'}
        topic2 = {'id': 2, 'url': 'http://2', 'display_name': '2', 'search_name': '2', 'quality': '720p'}
        topic3 = {'id': 3, 'url': 'http://3', 'display_name': '3', 'search_name': '3', 'season_number': 1, 'quality': '1080p'}
        topic4 = {'id': 4, 'url': 'http://4', 'display_name': '4', 'search_name': '4', 'season_number': 1, 'episode_number': 1, 'quality': 'SD'}
        topic5 = {'id': 5, 'url': 'http://5', 'display_name': '5', 'search_name': '5', 'season_number': 1, 'episode_number': 1, 'quality': '720p', 'last_update': datetime.now(pytz.utc)}

        lostfilm_topic1 = {'id': 1, 'search_name': '1', 'quality': 'SD'}
        lostfilm_topic2 = {'id': 2, 'search_name': '2', 'quality': '720p'}
        lostfilm_topic3 = {'id': 3, 'search_name': '3', 'season': 1, 'quality': '1080p'}
        lostfilm_topic4 = {'id': 4, 'search_name': '4', 'season': 1, 'episode': 1, 'quality': 'SD'}
        lostfilm_topic5 = {'id': 5, 'search_name': '5', 'season': 1, 'episode': 1, 'quality': '720p', 'last_update': datetime.now(pytz.utc)}

        topics = [topic1, topic2, topic3, topic4, topic5]
        lostfilm_topics = [lostfilm_topic1, lostfilm_topic2, lostfilm_topic3, lostfilm_topic4, lostfilm_topic5]

        self._upgrade_from([lostfilm_topics, topics], 2)

    def test_updage_filled2_from_version_2(self):
        topic1 = {'id': 1, 'url': 'http://1', 'display_name': '1', 'search_name': '1', 'quality': 'SD'}
        topic2 = {'id': 2, 'url': 'http://2', 'display_name': '2', 'search_name': '2', 'quality': '720p'}
        topic3 = {'id': 3, 'url': 'http://3', 'display_name': '3', 'search_name': '3', 'season_number': 1, 'quality': '1080p'}
        topic4 = {'id': 4, 'url': 'http://4', 'display_name': '4', 'search_name': '4', 'season_number': 1, 'episode_number': 1, 'quality': 'SD'}
        topic5 = {'id': 5, 'url': 'http://5', 'display_name': '5', 'search_name': '5', 'season_number': 1, 'episode_number': 1, 'quality': '720p', 'last_update': datetime.now(pytz.utc)}

        lostfilm_topic1 = {'id': 1, 'search_name': '1', 'quality': 'SD'}
        lostfilm_topic2 = {'id': 2, 'search_name': '2', 'quality': '720p'}
        lostfilm_topic3 = {'id': 3, 'search_name': '3', 'season': 1, 'quality': '1080p'}
        lostfilm_topic4 = {'id': 4, 'search_name': '4', 'season': 1, 'episode': 1, 'quality': 'SD'}
        lostfilm_topic5 = {'id': 5, 'search_name': '5', 'season': 1, 'episode': 1, 'quality': '720p', 'last_update': datetime.now(pytz.utc)}

        cred = {'username': 'login', 'password': 'password'}

        topics = [topic1, topic2, topic3, topic4, topic5]
        lostfilm_topics = [lostfilm_topic1, lostfilm_topic2, lostfilm_topic3, lostfilm_topic4, lostfilm_topic5]

        self._upgrade_from([lostfilm_topics, topics, [cred]], 2)
