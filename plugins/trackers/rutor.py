import re
import requests
import datetime
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from utils.bittorrent import Torrent
from plugin_managers import register_plugin


class RutorOrgTopic(Base):
    __tablename__ = "rutororg_topics"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    hash = Column(String, nullable=False)
    last_update = Column(DateTime, nullable=True)


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

        return title

    def get_hash(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        download_url = "http://d.rutor.org/download/" + match.group(1)
        r = requests.get(download_url)
        t = Torrent(r.content)
        return t.info_hash


class RutorOrgPlugin(object):
    name = "rutor.org"

    def __init__(self):
        self.tracker = RutorOrgTracker()

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def add_watch(self, url, display_name=None):
        name = self.parse_url(url)
        if not name:
            return None
        if not display_name:
            display_name = name
        hash = self.tracker.get_hash(url)
        entry = RutorOrgTopic(name=display_name, url=url, hash=hash)
        with DBSession() as db:
            db.add(entry)
            db.commit()
            return entry.id

    def remove_watch(self, url):
        with DBSession() as db:
            return db.query(RutorOrgTopic).filter(RutorOrgTopic.url == url).delete()

    def get_watching_torrents(self):
        with DBSession() as db:
            topics = db.query(RutorOrgTopic).all()
            return [self._get_torrent_info(t) for t in topics]

    def execute(self, progress_reporter):
        progress_reporter("Start checking for rutor.org")
        with DBSession() as db:
            topics = db.query(RutorOrgTopic).all()
            for topic in topics:
                progress_reporter("Start checking for %s" % topic.name)
                torrent_hash = self.tracker.get_hash(topic.url)
                if not topic.last_update:
                    progress_reporter("Download new torrent for %s" % topic.name)
                    topic.last_update = datetime.datetime.now()
                elif torrent_hash != topic.hash:
                    progress_reporter("Torrent %s was changed" % topic.name)
                    topic.last_update = datetime.datetime.now()

    @staticmethod
    def _get_torrent_info(topic):
        return {
            "id": topic.id,
            "name": topic.name,
            "url": topic.url,
            "info": None,
            "last_update": topic.last_update.isoformat() if topic.last_update else None
        }

register_plugin('tracker', 'rutor.org', RutorOrgPlugin())
