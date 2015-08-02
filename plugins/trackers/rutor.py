import re
import requests
import datetime
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from db import Base, DBSession, row2dict
from utils.bittorrent import Torrent
from plugin_managers import register_plugin
from utils.downloader import download
from plugins import Topic
from plugins.trackers import TrackerPluginBase

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
    _regex = re.compile(ur'^http://rutor.org/torrent/(\d+)(/.*)?$')
    title_header = "rutor.org ::"

    def parse_url(self, url):
        match = self._regex.match(url)
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
        match = self._regex.match(url)
        if match is None:
            return None

        return "http://d.rutor.org/download/" + match.group(1)

    @staticmethod
    def _get_title(title):
        return {'original_name': title}


class RutorOrgPlugin(TrackerPluginBase):
    name = PLUGIN_NAME
    watch_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    def __init__(self):
        self.tracker = RutorOrgTracker()

    def parse_url(self, url):
        parsed_url = self.tracker.parse_url(url)
        if not parsed_url:
            return None
        settings = {
            'display_name': parsed_url['original_name']
        }

        return settings

    def add_watch(self, url, settings):
        display_name = settings.get('display_name', None) if settings else None
        title = self.parse_url(url)
        if not title:
            return None
        if not display_name:
            display_name = title['original_name']
        hash = self.tracker.get_hash(url)
        entry = RutorOrgTopic(display_name=display_name, url=url, hash=hash)
        with DBSession() as db:
            db.add(entry)
            db.commit()
            return entry.id

    def get_watch(self, id):
        with DBSession() as db:
            topic = db.query(RutorOrgTopic).filter(RutorOrgTopic.id == id).first()
            if topic is None:
                return None
            settings = {
                'url': topic.url,
                'display_name': topic.display_name,
            }
            return {'settings': settings, 'form': self.watch_form}

    def update_watch(self, id, settings):
        with DBSession() as db:
            topic = db.query(RutorOrgTopic).filter(RutorOrgTopic.id == id).first()
            if topic is None:
                return False
            topic.display_name = settings.get('display_name', topic.display_name)
        return True

    def remove_watch(self, url):
        with DBSession() as db:
            topic = db.query(RutorOrgTopic).filter(RutorOrgTopic.url == url).first()
            if topic is None:
                return False
            db.delete(topic)
            return True

    def get_watching_torrents(self):
        with DBSession() as db:
            topics = db.query(RutorOrgTopic).all()
            return [self._get_torrent_info(t) for t in topics]

    def execute(self, engine):
        """

        :type engine: engine.Engine
        """
        engine.log.info(u"Start checking for <b>rutor.org</b>")
        with DBSession() as db:
            topics = db.query(RutorOrgTopic).all()
            db.expunge_all()
        for topic in topics:
            topic_name = topic.display_name
            try:
                engine.log.info(u"Check for changes <b>%s</b>" % topic_name)
                torrent_content, filename = download(self.tracker.get_download_url(topic.url))
                engine.log.downloaded(u"Torrent <b>%s</b> downloaded" % filename or topic_name, torrent_content)
                torrent = Torrent(torrent_content)
                if torrent.info_hash != topic.hash:
                    engine.log.info(u"Torrent <b>%s</b> was changed" % topic_name)
                    existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        engine.log.info(u"Torrent <b>%s</b> already added" % filename or topic_name)
                    elif engine.add_torrent(torrent_content):
                        old_existing_torrent = engine.find_torrent(topic.hash)
                        if old_existing_torrent:
                            engine.log.info(u"Updated <b>%s</b>" % filename or topic_name)
                        else:
                            engine.log.info(u"Add new <b>%s</b>" % filename or topic_name)
                        if old_existing_torrent:
                            if engine.remove_torrent(topic.hash):
                                engine.log.info(u"Remove old torrent <b>%s</b>" %
                                                old_existing_torrent['name'])
                            else:
                                engine.log.failed(u"Can't remove old torrent <b>%s</b>" %
                                                  old_existing_torrent['name'])
                        existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        last_update = existing_torrent['date_added']
                    else:
                        last_update = datetime.datetime.now()
                    with DBSession() as db:
                        db.add(topic)
                        topic.hash = torrent.info_hash
                        topic.last_update = last_update
                        db.commit()
                else:
                    engine.log.info(u"Torrent <b>%s</b> not changed" % topic_name)
            except Exception as e:
                engine.log.failed(u"Failed update <b>%s</b>.\nReason: %s" % (topic_name, e.message))
        engine.log.info(u"Finish checking for <b>rutor.org</b>")

    @staticmethod
    def _get_torrent_info(topic):
        return {
            "id": topic.id,
            "name": topic.display_name,
            "url": topic.url,
            "info": None,
            "last_update": topic.last_update
        }

register_plugin('tracker', PLUGIN_NAME, RutorOrgPlugin(), upgrade=upgrade)
