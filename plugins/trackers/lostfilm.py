# coding=utf-8
import re
import feedparser
import requests
import datetime
import copy
from requests import Session
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from db import Base, DBSession, row2dict
from urlparse import urlparse, parse_qs
from plugin_managers import register_plugin
from utils.bittorrent import Torrent
from utils.downloader import download
from plugins import Topic

PLUGIN_NAME = 'lostfilm.tv'

class LostFilmTVSeries(Topic):
    __tablename__ = "lostfilmtv_series"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    search_name = Column(String, nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    quality = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class LostFilmTVCredentials(Base):
    __tablename__ = "lostfilmtv_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    c_uid = Column('uid', String)
    c_pass = Column('pass', String)
    c_usess = Column('usess', String)
    default_quality = Column(String, nullable=False, server_default='SD')


def upgrade(engine, operations_factory, version):
    if engine.dialect.has_table(engine.connect(), LostFilmTVSeries.__tablename__):
        if version == -1:
            version = get_current_version(engine)
        if version == 0:
            with operations_factory() as operations:
                quality_column = Column('quality', String, nullable=False, server_default='SD')
                operations.add_column(LostFilmTVSeries.__tablename__, quality_column)
            version = 1
        if version == 1:
            upgrade_1_to_2(engine, operations_factory)
            version = 2
        if version == 2:
            with operations_factory() as operations:
                quality_column = Column('default_quality', String, nullable=False, server_default='SD')
                operations.add_column(LostFilmTVCredentials.__tablename__, quality_column)
            version = 3
    return version

def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(LostFilmTVSeries.__tablename__, m, autoload=True)
    credentials = Table(LostFilmTVCredentials.__tablename__, m, autoload=True)
    if 'default_quality' in credentials:
        return 3
    if 'quality' not in topics.columns:
        return 0
    if 'url' in topics.columns:
        return 1
    return 2

def upgrade_1_to_2(engine, operations_factory):
    # Version 1
    m1 = MetaData()
    LostFilmTVSeries1 = Table("lostfilmtv_series", m1,
                              Column('id', Integer, primary_key=True),
                              Column('display_name', String, unique=True, nullable=False),
                              Column('search_name', String, nullable=False),
                              Column('url', String, nullable=False, unique=True),
                              Column('season_number', Integer, nullable=True),
                              Column('episode_number', Integer, nullable=True),
                              Column('last_update', DateTime, nullable=True),
                              Column("quality", String, nullable=False, server_default='SD'))

    # Version 2
    m2 = MetaData(engine)
    TopicLast = Table('topics', m2, *[c.copy() for c in Topic.__table__.columns])
    LostFilmTVSeries2 = Table('lostfilmtv_series2', m2,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("search_name", String, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))

    def column_renames(concrete_topic, raw_topic):
        concrete_topic['season'] = raw_topic['season_number']
        concrete_topic['episode'] = raw_topic['episode_number']

    with operations_factory() as operations:
        if not engine.dialect.has_table(engine.connect(), TopicLast.name):
            TopicLast.create(engine)
        operations.upgrade_to_base_topic(LostFilmTVSeries1, LostFilmTVSeries2, PLUGIN_NAME,
                                         column_renames=column_renames)


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
                            ur'(\s+\[(?P<quality>[^\]]+)\])?\.\s+' +
                            ur'\((?P<episode_info>[^)]+)\)')
    _season_info = re.compile(ur'S(?P<season>\d{2})(E(?P<episode>\d{2}))+')
    login_url = "https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F"
    profile_url = 'http://www.lostfilm.tv/my.php'
    netloc = 'www.lostfilm.tv'

    def __init__(self, c_uid=None, c_pass=None, c_usess=None):
        self.c_uid = c_uid
        self.c_pass = c_pass
        self.c_usess = c_usess

    def setup(self, c_uid, c_pass, c_usess):
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
        cookies = self.get_cookies()
        if not cookies:
            return False
        r1 = requests.get('http://www.lostfilm.tv/my.php', cookies=cookies)
        return len(r1.text) > 0

    def get_cookies(self):
        if not self.c_uid or not self.c_pass or not self.c_usess:
            return False
        cookies = {'uid': self.c_uid, 'pass': self.c_pass, 'usess': self.c_usess}
        return cookies

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
        result['quality'] = LostFilmTVTracker._parse_quality(result['quality'])
        result.update({'season': int(season_info.group('season')), 'episode': int(season_info.group('episode'))})
        return result

    @staticmethod
    def _parse_quality(quality):
        if not quality:
            return 'SD'
        if quality == 'MP4':
            return '720p'
        if quality == '1080p':
            return '1080p'
        return 'unknown'

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
    name = PLUGIN_NAME
    settings_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'username',
            'label': 'Username',
            'flex': 45
        }, {
            "type": "password",
            "model": "password",
            "label": "Password",
            "flex": 45
        }, {
            "type": "select",
            "model": "default_quality",
            "label": "Default Quality",
            "options": ["SD", "720p", "1080p"],
            "flex": 10
        }]
    }]
    watch_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 70
        }, {
            "type": "select",
            "model": "quality",
            "label": "Quality",
            "options": ["SD", "720p", "1080p"],
            "flex": 30
        }]
    }]
    edit_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'number',
            'model': 'season',
            'label': 'Season',
            'flex': 40
        }, {
            'type': 'number',
            'model': 'episode',
            'label': 'Episode',
            'flex': 40
        }, {
            "type": "select",
            "model": "quality",
            "label": "Quality",
            "options": ["SD", "720p", "1080p"],
            "flex": 20
        }]
    }]

    def __init__(self):
        super(LostFilmPlugin, self).__init__()
        self.tracker = LostFilmTVTracker()

    def parse_url(self, url):
        parsed_url = self.tracker.parse_url(url)
        if not parsed_url:
            return None
        with DBSession() as db:
            cred = db.query(LostFilmTVCredentials).first()
            quality = cred.default_quality if cred else 'SD'
        settings = {
            'display_name': u"{} / {}".format(parsed_url['original_name'], parsed_url['name']),
            'quality': quality
        }

        return {'url': parsed_url, 'form': self.watch_form, 'settings': settings}

    def add_watch(self, url, settings):
        display_name = settings.get('display_name', None) if settings else None
        quality = settings.get('quality', 'SD') if settings else 'SD'

        title = self.tracker.parse_url(url)
        if not title:
            return None
        if not display_name:
            if 'name' in title:
                display_name = u"{0} / {1}".format(title['name'], title['original_name'])
            else:
                display_name = title['original_name']
        entry = LostFilmTVSeries(search_name=title['original_name'], display_name=display_name, url=url,
                                 season=None, episode=None, quality=quality)
        with DBSession() as db:
            db.add(entry)
            db.commit()
            return entry.id

    def get_watch(self, id):
        with DBSession() as db:
            topic = db.query(LostFilmTVSeries).filter(LostFilmTVSeries.id == id).first()
            if topic is None:
                return None
            return {'settings': row2dict(topic), 'form': self.edit_form}

    def update_watch(self, id, settings):
        with DBSession() as db:
            topic = db.query(LostFilmTVSeries).filter(LostFilmTVSeries.id == id).first()
            if topic is None:
                return False
            season = settings.get('season', topic.season)
            episode = settings.get('episode', topic.episode)
            topic.display_name = settings.get('display_name', topic.display_name)
            topic.quality = settings.get('quality', topic.quality)
            topic.season = int(season) if season else None
            topic.episode = int(episode) if episode else None

    def get_settings_form(self):
        return self.settings_form

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(LostFilmTVCredentials).first()
            if not cred:
                return None
            return {'username': cred.username, 'default_quality': cred.default_quality}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(LostFilmTVCredentials).first()
            if not cred:
                cred = LostFilmTVCredentials()
                db.add(cred)
            cred.username = settings['username']
            cred.password = settings['password']
            cred.default_quality = settings.get('default_quality', 'SD')

    def check_connection(self):
        return self._login_to_tracker()

    def remove_watch(self, url):
        with DBSession() as db:
            topic = db.query(LostFilmTVSeries).filter(LostFilmTVSeries.url == url).first()
            if topic is None:
                return False
            db.delete(topic)
            return True

    def get_watching_torrents(self):
        with DBSession() as db:
            series = db.query(LostFilmTVSeries).all()
            return [self._get_torrent_info(s) for s in series]

    def execute(self, engine):
        engine.log.info(u"Start checking for <b>lostfilm.tv</b>")
        try:
            if not self._login_to_tracker(engine):
                engine.log.failed('Login to <b>lostfilm.tv</b> failed')
                return
            cookies = self.tracker.get_cookies()
            with DBSession() as db:
                db_series = db.query(LostFilmTVSeries).all()
                series = map(row2dict, db_series)
            series_names = {s['search_name'].lower(): s for s in series}
            d = feedparser.parse(u'http://www.lostfilm.tv/rssdd.xml')
            engine.log.info(u'Download <a href="http://www.lostfilm.tv/rssdd.xml">rss</a>')
            try:
                for entry in d.entries:
                    info = self.tracker.parse_rss_title(entry.title)
                    if not info:
                        engine.log.failed(u'Can\'t parse title: <b>{0}</b>'.format(entry.title))
                        continue

                    original_name = info['original_name']
                    serie = series_names.get(original_name.lower(), None)

                    if not serie:
                        engine.log.info(u'Not watching series: {0}'.format(original_name))
                        continue

                    if (info['season'] < serie['season']) or \
                       (info['season'] == serie['season'] and info['episode'] <= serie['episode']):
                        engine.log.info(u"Series <b>{0}</b> not changed".format(original_name))
                        continue

                    if info['quality'] != serie['quality']:
                        engine.log.info(u'Skip <b>{0}</b> by quality filter. Searching for {1} by get {2}'
                                        .format(original_name, serie['quality'], info['quality']))
                        continue

                    try:
                        torrent_content, filename = download(entry.link, cookies=cookies)
                    except Exception as e:
                        engine.log.failed(u"Failed to download from <b>{0}</b>.\nReason: {1}"
                                          .format(entry.link, e.message))
                        continue
                    torrent = Torrent(torrent_content)
                    engine.log.downloaded(u'Download new series: {0} ({1})'
                                          .format(original_name, info['episode_info']),
                                          torrent_content)
                    existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        engine.log.info(u"Torrent <b>%s</b> already added" % filename or original_name)
                    elif engine.add_torrent(torrent_content):
                        engine.log.info(u"Add new <b>%s</b>" % filename or original_name)
                        existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        last_update = existing_torrent['date_added']
                    else:
                        last_update = datetime.datetime.now()
                    with DBSession() as db:
                        db_serie = db.query(LostFilmTVSeries)\
                            .filter(LostFilmTVSeries.id == serie['id'])\
                            .first()
                        db_serie.last_update = last_update
                        db_serie.season = info['season']
                        db_serie.episode = info['episode']
                        db.commit()
            except Exception as e:
                engine.log.failed(u"Failed update <b>lostfilm</b>.\nReason: {0}".format(e.message))
        finally:
            engine.log.info(u"Finish checking for <b>lostfilm.tv</b>")

    def _login_to_tracker(self, engine=None):
        with DBSession() as db:
            cred = db.query(LostFilmTVCredentials).first()
            if not cred:
                return False
            username = cred.username
            password = cred.password
            if not username or not password:
                return False
            self.tracker.setup(cred.c_uid, cred.c_pass, cred.c_usess)
        if self.tracker.verify():
            if engine:
                engine.log.info('Cookies are valid')
            return True
        if engine:
            engine.log.info('Login to <b>lostfilm.tv</b>')
        try:
            self.tracker.login(username, password)
            with DBSession() as db:
                cred = db.query(LostFilmTVCredentials).first()
                cred.c_uid = self.tracker.c_uid
                cred.c_pass = self.tracker.c_pass
                cred.c_usess = self.tracker.c_usess
        except Exception as e:
            if engine:
                engine.log.failed('Login to <b>lostfilm.tv</b> failed: {0}'.format(e.message))
        return self.tracker.verify()

    @staticmethod
    def _get_torrent_info(series):
        if series.season and series.episode:
            info = "S%02dE%02d" % (series.season, series.episode)
        elif series.season:
            info = "S%02d" % series.season
        else:
            info = None
        return {
            "id": series.id,
            "name": series.display_name,
            "url": series.url,
            "info": info,
            "last_update": series.last_update
        }

register_plugin('tracker', PLUGIN_NAME, LostFilmPlugin(), upgrade=upgrade)
