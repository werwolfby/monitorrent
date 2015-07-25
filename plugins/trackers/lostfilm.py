# coding=utf-8
import re
import feedparser
import requests
from requests import Session
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from urlparse import urlparse, parse_qs
from plugin_managers import register_plugin
from utils.downloader import download


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
    _regex = re.compile(ur'http://www\.lostfilm\.tv/browse\.php\?cat=\d+')
    search_usess_re = re.compile(ur'\(usess=([a-f0-9]{32})\)', re.IGNORECASE)
    _rss_title = re.compile(ur'(?P<name>[^(]+)\s+\((?P<original_name>[^(]+)\)\.\s+' +
                            ur'(?P<title>[^(]+)\s+\((?P<original_title>[^(]+)\)' +
                            ur'(\s+\[(?P<format>[^\]]+)\])?\.\s+' +
                            ur'\((?P<episode_info>[^)]+)\)')
    _season_info = re.compile(ur'S(?P<season>\d{2})(E(?P<episode>\d{2}))+')
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

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text)
        title = soup.title.string.strip()
        return self._parse_title(title)

    @staticmethod
    def parse_rss_title( title):
        """
        :param title: unicode
        :return: dict
        """
        m = LostFilmTVTracker._rss_title.match(title)
        if not m:
            return None
        result = m.groupdict()
        season_info = LostFilmTVTracker._season_info.match(result['episode_info'])
        if not season_info:
            return None
        result.update({'season': int(season_info.group('season')), 'episode': int(season_info.group('episode'))})
        return result

    @staticmethod
    def _parse_title(title):
        """
        :type title: unicode
        """
        bracket_index = title.index('(')
        if bracket_index < 0:
            return {'original_name': title}
        name = title[:bracket_index-1].strip()
        original_name = title[bracket_index+1:-1].strip()
        return {'name': name, 'original_name': original_name}


class LostFilmPlugin(object):
    name = "lostfilm.tv"

    def __init__(self):
        super(LostFilmPlugin, self).__init__()
        self.tracker = LostFilmTVTracker()

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def add_watch(self, url, display_name=None):
        title = self.parse_url(url)
        if not title:
            return None
        if not display_name:
            if 'name' in title:
                display_name = u"{0} / {1}".format(title['name'], title['original_name'])
            else:
                display_name = title['original_name']
        entry = LostFilmTVSeries(search_name=title['original_name'], display_name=display_name, url=url,
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

    def execute(self, engine):
        engine.log.info(u"Start checking for <b>lostfilm.tv</b>")
        with DBSession() as db:
            series = db.query(LostFilmTVSeries).all()
            db.expunge_all()
        series_names = dict([(s.search_name.lower(), s) for s in series])
        d = feedparser.parse(u'http://www.lostfilm.tv/rssdd.xml')
        engine.log.info(u'Download <a href="http://www.lostfilm.tv/rssdd.xml">rss</a>')
        try:
            for entry in d.entries:
                info = self.tracker.parse_rss_title(entry.title)
                if not info:
                    engine.log.failed(u'Can\'t parse title: <b>{0}</b>'.format(entry.title))
                original_name = info['original_name']
                serie = series_names.get(original_name.lower(), None)
                if not serie:
                    engine.log.info(u'Not watching series: {0}'.format(original_name))
                elif (info['season'] > serie.season_number) or \
                     (info['season'] == serie.season_number and info['episode'] > serie.episode_number):
                    #torrent_content, filename = download(entry.link)
                    engine.log.info(u'Download new series: {0} ({1})'.format(original_name, info['episode_info']))
                else:
                    engine.log.info(u"Series <b>{0}</b> not changed".format(original_name))
        except Exception as e:
            engine.log.failed(u"Failed update <b>lostfilm</b>.\nReason: {0}".format(e.message))
        engine.log.info(u"Finish checking for <b>lostfilm.tv</b>")

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
            "last_update": series.last_update.isoformat() if series.last_update else None
        }

register_plugin('tracker', 'lostfilm.tv', LostFilmPlugin())
