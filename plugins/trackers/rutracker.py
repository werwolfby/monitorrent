import re
from bs4 import BeautifulSoup
import requests
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from plugin_managers import register_plugin
from plugins.trackers.tracker_base import RutorLike
from utils.bittorrent import Torrent


class RutrackerTopic(Base):
    __tablename__ = "rutracker_topics"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    hash = Column(String, nullable=False)
    last_update = Column(DateTime, nullable=True)


class Rutracker(object):
    _regex = re.compile(ur'^http://w*\.*rutracker.org/forum/viewtopic.php\?t=(\d+)(/.*)?$')
    title_header = u'rutracker.org'

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        # without slash response gets fucked up
        if not url.endswith("/"):
            url += "/"
        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text)
        title = soup.title.string.strip()
        if title.lower().startswith(self.title_header):
            title = title[len(self.title_header):].strip()

        return title

    def get_hash(self, url, request_parameters):
        download_url = self.get_download_url(url)
        if not download_url:
            return None
        r = requests.post(download_url, request_parameters)
        t = Torrent(r.content)
        return t.info_hash

    def get_id(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        return match.group(1)

    def get_download_url(self, url):
        id = self.get_id(url)
        if id is None:
            return None
        return "http://dl.rutracker.org/forum/dl.php?t=" + id


class RutrackerPlugin(RutorLike):
    def get_request_paramerets(self, topic):
        return {'headers': {'referer': topic.url, 'host': "dl.rutracker.org"},
                'cookies': {'bb_data': "INSERT CRED HERE"}}

    @property
    def get_topic_type(self):
        return RutrackerTopic

    @property
    def get_tracker(self):
        return self.tracker

    @property
    def get_method(self):
        return requests.post

    def __init__(self):
        self.tracker = Rutracker()

    def parse_url(self, url):
        return self.get_tracker.parse_url(url)

    def add_watch(self, url, display_name=None):
        name = self.parse_url(url)
        if not name:
            return None
        if not display_name:
            display_name = name
        hash = self.get_tracker.get_hash(url, self.get_request_paramerets(RutrackerTopic(url=url)))
        entry = self.get_topic_type(name=display_name, url=url, hash=hash)
        with DBSession() as db:
            db.add(entry)
            db.commit()
            return entry.id

    def remove_watch(self, url):
        with DBSession() as db:
            return db.query(self.get_topic_type).filter(self.get_topic_type.url == url).delete()

    def get_watching_torrents(self):
        with DBSession() as db:
            topics = db.query(self.get_topic_type).all()
            return [self._get_torrent_info(t) for t in topics]

    def execute(self, engine):
        """

        :type engine: engine.Engine
        """
        engine.log.info(u"Start checking for <b>rutracker.org</b>")
        super(RutrackerPlugin, self).execute(engine)
        engine.log.info(u"Finish checking for <b>rutracker.org</b>")


register_plugin('tracker', 'rutracker.org', RutrackerPlugin())
