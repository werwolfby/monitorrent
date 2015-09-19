import re
import requests
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from monitorrent.db import row2dict
from monitorrent.utils.soup import get_soup
from monitorrent.utils.bittorrent import Torrent
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, ExecuteWithHashChangeMixin
from urlparse import urlparse

PLUGIN_NAME = 'rutor.org'


class RutorOrgTopic(Topic):
    __tablename__ = "rutororg_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), RutorOrgTopic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        upgrade_0_to_1(engine, operations_factory)
        version = 1
    if version == 1:
        upgrade_1_to_2(operations_factory)
        version = 2


def get_current_version(engine):
    m = MetaData(engine)
    t = Table(RutorOrgTopic.__tablename__, m, autoload=True)
    if 'url' in t.columns:
        return 0
    if 'hash' in t.columns and not t.columns['hash'].nullable:
        return 1
    return 2


def upgrade_0_to_1(engine, operations_factory):
    m0 = MetaData()
    rutor_topic_0 = Table("rutororg_topics", m0,
                          Column('id', Integer, primary_key=True),
                          Column('name', String, unique=True, nullable=False),
                          Column('url', String, nullable=False, unique=True),
                          Column('hash', String, nullable=False),
                          Column('last_update', DateTime, nullable=True))

    m1 = MetaData()
    topic_last = Table('topics', m1, *[c.copy() for c in Topic.__table__.columns])
    rutor_topic_1 = Table('rutororg_topics1', m1,
                          Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                          Column("hash", String, nullable=False))

    def topic_mapping(topic_values, raw_topic):
        topic_values['display_name'] = raw_topic['name']

    with operations_factory() as operations:
        if not engine.dialect.has_table(engine.connect(), topic_last.name):
            topic_last.create(engine)
        operations.upgrade_to_base_topic(rutor_topic_0, rutor_topic_1, PLUGIN_NAME,
                                         topic_mapping=topic_mapping)


def upgrade_1_to_2(operations_factory):
    m1 = MetaData()
    rutor_topic_1 = Table('rutororg_topics', m1,
                          Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                          Column("hash", String, nullable=False))

    m2 = MetaData()
    rutor_topic_2 = Table('rutororg_topics2', m2,
                          Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                          Column("hash", String, nullable=True))
    with operations_factory() as operations:
        operations.create_table(rutor_topic_2)
        topics = operations.db.query(rutor_topic_1)
        for topic in topics:
            raw_topic = row2dict(topic, rutor_topic_1)
            operations.db.execute(rutor_topic_2.insert(), raw_topic)
        operations.drop_table(rutor_topic_1)
        operations.rename_table(rutor_topic_2.name, rutor_topic_1.name)


class RutorOrgTracker(object):
    tracker_domain = 'rutor.org'
    _regex = re.compile(ur'^/torrent/(\d+)(/.*)?$')
    title_header = "rutor.org ::"

    def can_parse_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc.endswith('.' + self.tracker_domain) or parsed_url.netloc == self.tracker_domain

    def parse_url(self, url):
        if not self.can_parse_url(url):
            return None
        parsed_url = urlparse(url)
        match = self._regex.match(parsed_url.path)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None
        r.encoding = 'utf-8'
        soup = get_soup(r.text)
        title = soup.title.string.strip()
        if title.lower().startswith(self.title_header):
            title = title[len(self.title_header):].strip()

        return self._get_title(title)

    def get_hash(self, url):
        download_url = self.get_download_url(url)
        if not download_url:
            return None
        r = requests.get(download_url, allow_redirects=False)
        content_type = r.headers.get('content-type', '')
        if content_type.find('bittorrent') == -1:
            raise Exception('Expect torrent for download from url: {0}, but was {1}'.format(url, content_type))
        t = Torrent(r.content)
        return t.info_hash

    def get_download_url(self, url):
        if not self.can_parse_url(url):
            return None
        parsed_url = urlparse(url)
        match = self._regex.match(parsed_url.path)
        if match is None:
            return None

        return "http://d.rutor.org/download/" + match.group(1)

    @staticmethod
    def _get_title(title):
        return {'original_name': title}


class RutorOrgPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = RutorOrgTracker()
    topic_class = RutorOrgTopic
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        return self.tracker.get_download_url(topic.url)


register_plugin('tracker', PLUGIN_NAME, RutorOrgPlugin(), upgrade=upgrade)
