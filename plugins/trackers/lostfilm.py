import re
import requests
from requests import Session
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, Session as DBSession
from urlparse import urlparse, parse_qs
from plugin_managers import register_plugin


class LostFilmTVSeries(Base):
    __tablename__ = "lostfilmtv_series"

    id = Column(Integer, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    search_name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    season_number = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)
    last_update = Column(DateTime, nullable=True)


class LostFilmTVCredentials(Base):
    __tablename__ = "lostfilmtv_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    c_uid = Column('uid', String)
    c_pass = Column('pass', String)
    c_usess = Column('usess', String)


class LostFilmTVException(Exception):
    pass


class LostFilmTVLoginFailedException(Exception):
    def __init__(self, code, text, message):
        self.code = code
        self.text = text
        self.message = message


class LostFilmTVTracker(object):
    search_usess_re = re.compile(ur'\(usess=([a-f0-9]{32})\)', re.IGNORECASE)
    login_url = "https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F"
    profile_url = 'http://www.lostfilm.tv/my.php'
    netloc = 'www.lostfilm.tv'

    def __init__(self, c_uid = None, c_pass = None, c_usess = None):
        self.c_uid = c_uid
        self.c_pass = c_pass
        self.c_usess = c_usess

    def login(self, username, password):
        s = Session()
        # login over bogi.ru
        params = {"login": username, "password": password}
        r1 = s.post(self.login_url, params, verify=False)
        # in case of failed login, bogi redirects to:
        # http://www.lostfilm.tv/blg.php?code=6&text=incorrect%20login/password
        if r1.request.url != self.login_url:
            url = urlparse(r1.url)
            if url.netloc == self.netloc:
                query = parse_qs(url.query)
                code = int(query.get('code', ['-1'])[0])
                text = query.get('text', "-")
                r1.encoding = 'windows-1251'
                message = r1.text
                raise LostFilmTVLoginFailedException(code, text, message)
            else:
                raise LostFilmTVLoginFailedException(-1, None, None)

        # callback to lostfilm.tv
        soup = BeautifulSoup(r1.text)
        inputs = soup.findAll("input")
        action = soup.find("form")['action']
        cparams = dict([(i['name'], i['value']) for i in inputs if 'value' in i.attrs])
        s.post(action, cparams, verify=False)

        # call to profile page
        r3 = s.get(self.profile_url)

        # read required params
        self.c_uid = s.cookies['uid']
        self.c_pass = s.cookies['pass']
        self.c_usess = self.search_usess_re.findall(r3.text)[0]

    def verify(self):
        cookies = {'uid': self.c_uid, 'pass': self.c_pass, 'usess': self.c_usess}
        r1 = requests.get('http://www.lostfilm.tv/my.php', cookies=cookies)
        return len(r1.text) > 0


class LostFilmPlugin(object):
    name = "lostfilm.tv"

    _regex = re.compile(ur'http://www\.lostfilm\.tv/browse\.php\?cat=\d+')
    _search_usess_re = re.compile(ur'\(usess=([a-f0-9]{32})\)', re.IGNORECASE)

    def __init__(self):
        super(LostFilmPlugin, self).__init__()

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text)
        title = soup.title.string.strip()
        return title

    def add_watch(self, url, display_name=None):
        search_name = self.parse_url(url)
        if not search_name:
            return None
        if not display_name:
            display_name = search_name
        entry = LostFilmTVSeries(search_name=search_name, display_name=display_name, url=url,
                                 season_number=None, episode_number=None)
        with DBSession() as db:
            db.add(entry)
            db.commit()
            return entry.id

    def remove_watch(self, url):
        with DBSession() as db:
            return db.query(LostFilmTVSeries).filter(LostFilmTVSeries.url == url).delete()

    def get_watching_torrents(self):
        with DBSession() as db:
            series = db.query(LostFilmTVSeries).all()
            return [self._get_torrent_info(s) for s in series]

    @staticmethod
    def _get_torrent_info(series):
        if series.season_number and series.episode_number:
            info = "S%02dE%02d" % (series.season_number, series.episode_number)
        elif series.season_number:
            info = "S%02d" % series.season_number
        else:
            info = None
        return {
            "id": series.id,
            "name": series.display_name,
            "url": series.url,
            "info": info,
            "last_update": series.last_update
        }

register_plugin('tracker', 'lostfilm.tv', LostFilmPlugin())
