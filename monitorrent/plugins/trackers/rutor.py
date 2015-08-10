import re
import requests
import datetime
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from monitorrent.db import Base, DBSession, row2dict
from monitorrent.utils.bittorrent import Torrent
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.downloader import download
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase
from urlparse import urlparse

PLUGIN_NAME = 'rutor.org'


class RutorOrgTopic(Topic):
    __tablename__ = "rutororg_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }

def upgrade(engine, operations_factory, version):
    if engine.dialect.has_table(engine.connect(), RutorOrgTopic.__tablename__):
        if version == -1:
            version = get_current_version(engine)
        if version == 0:
            upgrade_0_to_1(engine, operations_factory)
            version = 1
    return version

def get_current_version(engine):
    m = MetaData(engine)
    t = Table(RutorOrgTopic.__tablename__, m, autoload=True)
    if 'url' in t.columns:
        return 0
    return 1

def upgrade_0_to_1(engine, operations_factory):
    m0 = MetaData()
    RutorOrgTopic0 = Table("rutororg_topics", m0,
                           Column('id', Integer, primary_key=True),
                           Column('name', String, unique=True, nullable=False),
                           Column('url', String, nullable=False, unique=True),
                           Column('hash', String, nullable=False),
                           Column('last_update', DateTime, nullable=True))

    m1 = MetaData()
    TopicLast = Table('topics', m1, *[c.copy() for c in Topic.__table__.columns])
    RutorOrgTopic1 = Table('rutororg_topics1', m1,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=False))

    def topic_mapping(topic_values, raw_topic):
        topic_values['display_name'] = raw_topic['name']

    with operations_factory() as operations:
        if not engine.dialect.has_table(engine.connect(), TopicLast.name):
            TopicLast.create(engine)
        operations.upgrade_to_base_topic(RutorOrgTopic0, RutorOrgTopic1, PLUGIN_NAME,
                                         topic_mapping=topic_mapping)


class RutorOrgTracker(object):
    _regex = re.compile(ur'^/torrent/(\d+)(/.*)?$')
    title_header = "rutor.org ::"

    def can_parse_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc.endswith('.rutor.org') or parsed_url.netloc == 'rutor.org'

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
        soup = BeautifulSoup(r.text)
        title = soup.title.string.strip()
        if title.lower().startswith(self.title_header):
            title = title[len(self.title_header):].strip()

        return self._get_title(title)

    def get_hash(self, url):
        download_url = self.get_download_url(url)
        if not download_url:
            return None
        r = requests.get(download_url)
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


class RutorOrgPlugin(TrackerPluginBase):
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
        return self.tracker.parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        return self.tracker.get_download_url(topic.url)

    def _set_topic_params(self, url, parsed_url, topic, params):
        super(RutorOrgPlugin, self)._set_topic_params(url, parsed_url, topic, params)
        if url is not None:
            hash_value = self.tracker.get_hash(url)
            topic.hash = hash_value


register_plugin('tracker', PLUGIN_NAME, RutorOrgPlugin(), upgrade=upgrade)
