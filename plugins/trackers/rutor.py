import re
import requests
import datetime
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from utils.bittorrent import Torrent
from plugin_managers import register_plugin
from utils.downloader import download


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

    def execute(self, engine):
        """

        :type engine: engine.Engine
        """
        engine.log.info(u"Start checking for <b>rutor.org</b>")
        with DBSession() as db:
            topics = db.query(RutorOrgTopic).all()
            db.expunge_all()
        for topic in topics:
            topic_name = topic.name
            try:
                engine.log.info(u"Check for changes <b>%s</b>" % topic_name)
                torrent, filename = download(self.tracker.get_download_url(topic.url))
                engine.log.downloaded(u"Torrent <b>%s</b> downloaded" % filename or topic_name, torrent)
                t = Torrent(torrent)
                if t.info_hash != topic.hash:
                    engine.log.info(u"Torrent <b>%s</b> was changed" % topic_name)
                    date_added = engine.find_torrent(t.info_hash)
                    if date_added:
                        engine.log.info(u"Torrent <b>%s</b> already added" % filename or topic_name)
                    elif engine.add_torrent(torrent):
                        date_added = engine.find_torrent(topic.hash)
                        if date_added:
                            engine.log.info(u"Updated <b>%s</b>" % filename or topic_name)
                        else:
                            engine.log.info(u"Add new <b>%s</b>" % filename or topic_name)
                        if date_added:
                            if engine.remove_torrent(topic.hash):
                                engine.log.info(u"Remove old torrent by hash <b>%s</b>" % topic.hash)
                            else:
                                engine.log.failed(u"Can't remove old torrent by hash <b>%s</b>" % topic.hash)
                    with DBSession() as db:
                        db.add(topic)
                        topic.hash = t.info_hash
                        topic.last_update = datetime.datetime.now()
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
            "name": topic.name,
            "url": topic.url,
            "info": None,
            "last_update": topic.last_update.isoformat() if topic.last_update else None
        }

register_plugin('tracker', 'rutor.org', RutorOrgPlugin())
