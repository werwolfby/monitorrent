import re
from bs4 import BeautifulSoup
from pip._vendor.requests import Session
import requests
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from plugin_managers import register_plugin
from plugins.trackers.tracker_base import TrackerBase
from utils.bittorrent import Torrent


class RutrackerCredentials(Base):
    __tablename__ = "rutracker_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)


class RutrackerLoginFailedException(Exception):
    def __init__(self, message):
        self.message = message


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
        r = requests.post(download_url, **request_parameters)
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


class RutrackerPlugin(TrackerBase):
    name = "rutracker.org"
    login_url = "http://login.rutracker.org/forum/login.php"

    cookie_name = "bb_data"
    cookie = None
    uid = None
    uid_regex = re.compile(ur'\d*-(\d*)-.*')
    profile_page = "http://rutracker.org/forum/profile.php?mode=viewprofile&u={}"

    def login(self, username, password):
        s = Session()
        login_result = s.post(self.login_url,
                              {"login_username": username, "login_password": password, 'login': '%C2%F5%EE%E4'},
                              verify=False)
        if login_result.url.startswith(self.login_url):
            # TODO get error info (although it shouldn't contain anything useful
            raise RutrackerLoginFailedException("Invalid login or password")
        else:
            cookie = s.cookies.get(self.cookie_name)
            if not cookie:
                raise RutrackerLoginFailedException("Failed to retrieve cookie")

            self.cookie = cookie
            self.uid = self.uid_regex.match(cookie).group(1)

    def verify(self):
        profile_page_url = self.profile_page.format(self.uid)
        profile_page_result = requests.get(profile_page_url, cookies={self.cookie_name: self.cookie})
        return profile_page_result.url == profile_page_url

    def get_request_paramerets(self, topic):
        return {'headers': {'referer': topic.url, 'host': "dl.rutracker.org"},
                'cookies': {self.cookie_name: self.cookie}}

    @property
    def get_topic_type(self):
        return RutrackerTopic

    @property
    def get_tracker(self):
        return self.tracker

    @property
    def get_method(self):
        return requests.post

    @property
    def get_credentials_type(self):
        return RutrackerCredentials

    def __init__(self):
        self.tracker = Rutracker()

    def parse_url(self, url):
        return self._get_title(self.get_tracker.parse_url(url))

    def add_watch(self, url, display_name=None):
        if not self._login_to_tracker():
            return None
        title = self.parse_url(url)
        if not title:
            return None
        if not display_name:
            display_name = title['original_name']
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
