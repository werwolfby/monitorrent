# coding=utf-8
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey, String

from monitorrent.db import DBSession, row2dict
from monitorrent.plugins import Topic, Status
from monitorrent.plugins.trackers.anilibria import upgrade, get_current_version
from monitorrent.settings_manager import ProxySettings, Settings
from tests import UpgradeTestCase, use_vcr


# noinspection PyPep8Naming
class AnilibriaTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    AnilibriaTopic0 = Table("anilibriatv_topics", m0,
                            Column("id", Integer, ForeignKey("topics.id"), primary_key=True),
                            Column("hash", String, nullable=True))

    m1 = MetaData()
    AnilibriaTopic1 = Table("anilibriatv_topics", m1,
                            Column("id", Integer, ForeignKey("topics.id"), primary_key=True),
                            Column("hash", String, nullable=True),
                            Column("format", String, nullable=True),
                            Column("format_list", String, nullable=True))
    BaseTopic0 = UpgradeTestCase.copy(Topic.__table__, m0)

    BaseTopic1 = UpgradeTestCase.copy(Topic.__table__, m1)

    versions = [
        (AnilibriaTopic0, BaseTopic0),
        (AnilibriaTopic1, BaseTopic1)
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

    def _test_empty_db_test(self):
        self._test_empty_db_test()

    def test_upgrade_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    @use_vcr()
    def test_upgrade_filled_from_version_0(self):
        topic1 = {'id': 1, 'url': 'https://www.anilibria.tv/release/seishun-buta-yarou-wa-bunny-girl-senpai-no-yume'
                                  '-wo-minai.html', 'display_name': '1', 'type': 'anilibria.tv'}
        anilibria_topic1 = {'id': 1, 'hash': 'abcdef'}
        topic2 = {'id': 2, 'url': 'https://www.anilibria.tv', 'display_name': '2', 'type': 'anilibria.tv'}
        anilibria_topic2 = {'id': 2, 'hash': 'abcdef'}

        self._upgrade_from([[anilibria_topic1, anilibria_topic2], [topic1, topic2]], 0)

        with DBSession() as db:
            topics = [row2dict(t, self.AnilibriaTopic1) for t in db.query(self.AnilibriaTopic1)]
            base_topics = [row2dict(t, self.BaseTopic1) for t in db.query(self.BaseTopic1)]

        assert topics[0]['format_list'] == u'HDTVRip 1080p,HDTVRip 720p'
        assert topics[0]['format'] == u'HDTVRip 1080p'
        assert base_topics[0]['status'] == Status.Ok

        assert base_topics[1]['status'] == Status.Error
