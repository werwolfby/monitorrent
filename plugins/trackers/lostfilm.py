import re
import requests
from requests import Session
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from urlparse import urlparse, parse_qs
from plugin_loader import register_plugin


class LostFilmTVSeries(Base):
    __tablename__ = "lostfilmtv_series"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    season_number = Column(Integer, nullable=False)
    episiode_number = Column(Integer, nullable=False)
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

#    def walk(self, db):
#        credentials = db.query(LostFilmTVCredentials).first()
#        if credentials is None or not credentials.username or not credentials.password:
#            return
#        if not credentials.cookies or not self.verify(credentials.c_uid, credentials.c_pass, credentials.c_usess):
#            self.login(credentials.username, credentials.password)
#        pass

register_plugin('tracker', 'lostfilm.tv', LostFilmPlugin())
