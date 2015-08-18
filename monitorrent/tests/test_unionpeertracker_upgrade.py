from monitorrent.plugins.trackers.unionpeer import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from monitorrent.tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class UnionpeerTrackerUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    TopicsLast0 = UpgradeTestCase.copy(Topic.__table__, m0)
    RutorOrgTopic0 = Table('unionpeerorg_topics', m0,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=False))

    m1 = MetaData()
    TopicsLast1 = UpgradeTestCase.copy(Topic.__table__, m1)
    RutorOrgTopic1 = Table('unionpeerorg_topics', m1,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=True))
    versions = [
        (RutorOrgTopic0, TopicsLast0),
        (RutorOrgTopic1, TopicsLast1),
    ]

    def _upgrade(self):
        return upgrade(self.engine, self.operation_factory)

    def _get_current_version(self):
        return get_current_version(self.engine)

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    def test_updage_filled_from_version_0(self):
        topic1 = {'id': 1, 'display_name': '1', 'url': 'http://1', 'last_update': None}
        topic2 = {'id': 2, 'display_name': '2', 'url': 'http://2', 'last_update': None}
        topic3 = {'id': 3, 'display_name': '3', 'url': 'http://3', 'last_update': None}

        tracker_topic1 = {'id': 1, 'hash': 'a1b'}
        tracker_topic2 = {'id': 2, 'hash': 'a2b'}
        tracker_topic3 = {'id': 3, 'hash': 'a3b'}

        topics = [topic1, topic2, topic3]
        tracker_topics = [tracker_topic1, tracker_topic2, tracker_topic3]

        self._upgrade_from([tracker_topics, topics], 0)
