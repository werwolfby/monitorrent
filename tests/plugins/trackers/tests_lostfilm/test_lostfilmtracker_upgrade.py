# coding=utf-8
import pytz
from monitorrent.db import UTCDateTime, row2dict, DBSession
from monitorrent.plugins.status import Status
from monitorrent.settings_manager import Settings, ProxySettings
from monitorrent.plugins.trackers.lostfilm import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from datetime import datetime
from tests import UpgradeTestCase, use_vcr
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
    Topic2 = UpgradeTestCase.copy(Topic.__table__, m2)
    LostFilmTVSeries2 = Table("lostfilmtv_series", m2,
                              Column('id', Integer, ForeignKey('topics.id'), primary_key=True),
                              Column('search_name', String, nullable=False),
                              Column('season', Integer, nullable=True),
                              Column('episode', Integer, nullable=True),
                              Column('quality', String, nullable=False, server_default='SD'))
    LostFilmTVCredentials2 = UpgradeTestCase.copy(LostFilmTVCredentials1, m2)
    m3 = MetaData()
    Topic3 = UpgradeTestCase.copy(Topic.__table__, m3)
    LostFilmTVSeries3 = UpgradeTestCase.copy(LostFilmTVSeries2, m3)
    LostFilmTVCredentials3 = Table("lostfilmtv_credentials", m3,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('uid', String),
                                   Column('pass', String),
                                   Column('usess', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))
    m4 = MetaData()
    Topic4 = UpgradeTestCase.copy(Topic.__table__, m4)
    LostFilmTVSeries4 = Table('lostfilmtv_series', m4,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("cat", Integer, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))
    LostFilmTVCredentials4 = Table("lostfilmtv_credentials", m4,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('session', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))
    m5 = MetaData()
    Topic5 = UpgradeTestCase.copy(Topic.__table__, m5)
    LostFilmTVSeries5 = Table('lostfilmtv_series', m5,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("cat", Integer, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))
    LostFilmTVCredentials5 = Table("lostfilmtv_credentials", m5,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('session', String),
                                   Column('cookies', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))

    versions = [
        (LostFilmTVSeries0, LostFilmTVCredentials0),
        (LostFilmTVSeries1, LostFilmTVCredentials1),
        (LostFilmTVSeries2, Topic2, LostFilmTVCredentials2),
        (LostFilmTVSeries3, Topic3, LostFilmTVCredentials3),
        (LostFilmTVSeries4, Topic4, LostFilmTVCredentials4),
        (LostFilmTVSeries5, Topic5, LostFilmTVCredentials5),
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

    def test_updage_empty_from_version_1(self):
        self._upgrade_from(None, 1)

    def test_updage_empty_from_version_2(self):
        self._upgrade_from(None, 2)

    def test_updage_empty_from_version_3(self):
        self._upgrade_from(None, 3)

    def test_updage_empty_from_version_4(self):
        self._upgrade_from(None, 4)

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

    @use_vcr()
    def test_updage_filled_from_version_3(self):
        Table('lostfilmtv_series4', self.m3,
              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
              Column("cat", Integer, nullable=False),
              Column("season", Integer, nullable=True),
              Column("episode", Integer, nullable=True),
              Column("quality", String, nullable=False))

        Table("lostfilmtv_credentials4", self.m3,
              Column('username', String, primary_key=True),
              Column('password', String, primary_key=True),
              Column('session', String),
              Column('default_quality', String, nullable=False, server_default='SD'))

        topic1 = {'id': 1, 'url': 'http://www.lostfilm.tv/browse.php?cat=236',
                  'display_name': u'12 обезьян / 12 Monkeys', 'type': 'lostfilm.tv'}
        topic2 = {'id': 2, 'url': 'http://www.lostfilm.tv/browse.php?cat=245',
                  'display_name': u'Mr. Robot', 'type': 'lostfilm.tv'}
        topic3 = {'id': 3, 'url': 'http://www.lostfilm.tv/browse.php?cat=251',
                  'display_name': u'Scream', 'type': 'lostfilm.tv'}
        topic4 = {'id': 4, 'url': 'https://www.lostfilm.tv/browse.php?cat=300',
                  'display_name': u'Emerald City', 'type': 'lostfilm.tv'}
        topic5 = {'id': 5, 'url': 'http://www.lostfilm.tv/browse.php?cat=_301',
                  'display_name': u'Taboo', 'type': 'lostfilm.tv'}
        topic6 = {'id': 6, 'url': 'http://www.lostfilm.tv/browse.php?cat=131',
                  'display_name': u'Broadwalk Empire', 'type': 'lostfilm.tv'}
        topic7 = {'id': 7, 'url': 'http://www.lostfilm.tv/random_url.php?cat=1',
                  'display_name': u'Random Show', 'type': 'lostfilm.tv'}

        lostfilm_topic1 = {'id': 1, 'search_name': '1', 'quality': 'SD'}
        lostfilm_topic2 = {'id': 2, 'search_name': '2', 'season': 2, 'quality': '720p'}
        lostfilm_topic3 = {'id': 3, 'search_name': '3', 'season': 1, 'episode': 3, 'quality': '1080p'}
        lostfilm_topic4 = {'id': 4, 'search_name': '4', 'season': 1, 'episode': 3, 'quality': '720p'}
        lostfilm_topic5 = {'id': 5, 'search_name': '5', 'quality': '720p'}
        lostfilm_topic6 = {'id': 6, 'search_name': '6', 'quality': '720p'}
        lostfilm_topic7 = {'id': 7, 'search_name': '7', 'quality': '720p'}

        cred = {'username': 'login', 'password': 'password'}

        topics = [topic1, topic2, topic3, topic4, topic5, topic6, topic7]
        lostfilm_topics = [lostfilm_topic1, lostfilm_topic2, lostfilm_topic3, lostfilm_topic4, lostfilm_topic5,
                           lostfilm_topic6, lostfilm_topic7]

        self._upgrade_from([lostfilm_topics, topics, [cred]], 3)

        with DBSession() as db:
            lostfilm_topics = [row2dict(t, self.LostFilmTVSeries4) for t in db.query(self.LostFilmTVSeries4)]
            lostfilm_topics = {t['id']: t for t in lostfilm_topics}

            topics4 = [row2dict(t, self.Topic4) for t in db.query(self.Topic4)]
            topics4 = {t['id']: t for t in topics4}

        assert len(lostfilm_topics) == 7
        assert lostfilm_topics[1]['cat'] == 236
        assert lostfilm_topics[2]['cat'] == 245
        assert lostfilm_topics[3]['cat'] == 251
        assert lostfilm_topics[4]['cat'] == 300
        assert lostfilm_topics[5]['cat'] == 301
        assert lostfilm_topics[6]['cat'] == 131
        assert lostfilm_topics[7]['cat'] == 0

        assert len(topics4) == 7
        assert topics4[1]['url'] == 'https://www.lostfilm.tv/series/12_Monkeys/seasons'
        assert topics4[1]['status'] == Status.Ok
        assert topics4[2]['url'] == 'https://www.lostfilm.tv/series/Mr_Robot/seasons'
        assert topics4[2]['status'] == Status.Ok
        assert topics4[3]['url'] == 'https://www.lostfilm.tv/series/Scream/seasons'
        assert topics4[3]['status'] == Status.Ok
        assert topics4[4]['url'] == 'https://www.lostfilm.tv/series/Emerald_City/seasons'
        assert topics4[4]['status'] == Status.Ok
        assert topics4[5]['url'] == 'https://www.lostfilm.tv/series/Taboo/seasons'
        assert topics4[5]['status'] == Status.Ok
        assert topics4[6]['url'] == 'http://www.lostfilm.tv/browse.php?cat=131'
        assert topics4[6]['status'] == Status.Error
        assert topics4[7]['url'] == 'http://www.lostfilm.tv/random_url.php?cat=1'
        assert topics4[7]['status'] == Status.Error

