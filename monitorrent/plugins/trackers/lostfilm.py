# coding=utf-8
import re
import feedparser
import requests
from requests import Session
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from monitorrent.db import Base, DBSession, row2dict
from urlparse import urlparse, parse_qs
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils import soup_factory
from monitorrent.utils.bittorrent import Torrent
from monitorrent.utils.downloader import download
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginWithCredentialsBase, LoginResult

PLUGIN_NAME = 'lostfilm.tv'


class LostFilmTVSeries(Topic):
    __tablename__ = "lostfilmtv_series"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    search_name = Column(String, nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    quality = Column(String, nullable=False, server_default='SD')

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


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), LostFilmTVSeries.__tablename__):
        return
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


def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(LostFilmTVSeries.__tablename__, m, autoload=True)
    credentials = Table(LostFilmTVCredentials.__tablename__, m, autoload=True)
    if 'quality' not in topics.columns:
        return 0
    if 'url' in topics.columns:
        return 1
    if 'default_quality' not in credentials.columns:
        return 2
    return 3


def upgrade_1_to_2(engine, operations_factory):
    # Version 1
    m1 = MetaData()
    lostfilm_series_1 = Table("lostfilmtv_series", m1,
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
    topic_last = Table('topics', m2, *[c.copy() for c in Topic.__table__.columns])
    lostfilm_series_2 = Table('lostfilmtv_series2', m2,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("search_name", String, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))

    def column_renames(concrete_topic, raw_topic):
        concrete_topic['season'] = raw_topic['season_number']
        concrete_topic['episode'] = raw_topic['episode_number']

    with operations_factory() as operations:
        if not engine.dialect.has_table(engine.connect(), topic_last.name):
            topic_last.create(engine)
        operations.upgrade_to_base_topic(lostfilm_series_1, lostfilm_series_2, PLUGIN_NAME,
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
                            ur'(?P<title>[^([]+)(\s+\((?P<original_title>[^(]+)\))?' +
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
                text = query.get('text', ["-"])[0]
                r1.encoding = 'windows-1251'
                message = r1.text
                raise LostFilmTVLoginFailedException(code, text, message)
            else:
                raise LostFilmTVLoginFailedException(-1, None, None)

        # callback to lostfilm.tv
        soup = soup_factory.get_soup(r1.text)
        inputs = soup.findAll("input")
        action = soup.find("form")['action']
        cparams = dict([(i['name'], i['value']) for i in inputs if 'value' in i.attrs])
        r2 = s.post(action, cparams, verify=False, allow_redirects=False)
        if r2.status_code != 302 and r2.headers['location'] != '/':
            raise LostFilmTVLoginFailedException(-2, None, None)

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

    def can_parse_url(self, url):
        return self._regex.match(url) is not None

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None
        soup = soup_factory.get_soup(r.text)
        title = soup.title.string.strip()
        return self._parse_title(title)

    @staticmethod
    def parse_rss_title(title):
        """
        :type title: str
        :rtype: dict | None
        """
        m = LostFilmTVTracker._rss_title.match(title)
        if not m:
            return None
        result = m.groupdict()
        season_info = LostFilmTVTracker._season_info.match(result['episode_info'])
        if not season_info:
            return None
        result['quality'] = LostFilmTVTracker._parse_quality(result['quality'])
        result['season'] = int(season_info.group('season'))
        result['episode'] = int(season_info.group('episode'))
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


class LostFilmPlugin(TrackerPluginWithCredentialsBase):
    tracker = LostFilmTVTracker()
    credentials_class = LostFilmTVCredentials
    credentials_public_fields = ['username', 'default_quality']
    credentials_private_fields = ['username', 'password', 'default_quality']
    credentials_form = [{
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
    topic_class = LostFilmTVSeries
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'season', 'episode', 'quality']
    topic_private_fields = ['display_name', 'season', 'episode', 'quality']
    topic_form = [{
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
    topic_edit_form = [{
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

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def prepare_add_topic(self, url):
        parsed_url = self.tracker.parse_url(url)
        if not parsed_url:
            return None
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            quality = cred.default_quality if cred else 'SD'
        settings = {
            'display_name': self._get_display_name(parsed_url),
            'quality': quality
        }

        return settings

    def login(self):
        """
        :rtype: LoginResult
        """
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return LoginResult.CredentialsNotSpecified
            username = cred.username
            password = cred.password
            if not username or not password:
                return LoginResult.CredentialsNotSpecified
        try:
            self.tracker.login(username, password)
            with DBSession() as db:
                cred = db.query(self.credentials_class).first()
                cred.c_uid = self.tracker.c_uid
                cred.c_pass = self.tracker.c_pass
                cred.c_usess = self.tracker.c_usess
            return LoginResult.Ok
        except LostFilmTVLoginFailedException as e:
            if e.code == 6:
                return LoginResult.IncorrentLoginPassword
            return LoginResult.Unknown
        except Exception:
            # TODO: Log unexpected excepton
            return LoginResult.Unknown

    def verify(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return False
            username = cred.username
            password = cred.password
            if not username or not password or \
                    not cred.c_uid or not cred.c_pass or not cred.c_usess:
                return False
            self.tracker.setup(cred.c_uid, cred.c_pass, cred.c_usess)
        return self.tracker.verify()

    def execute(self, ids, engine):
        """

        :type ids: list[int] | None
        :type engine: engine.Engine
        :rtype: None
        """
        if not self._execute_login(engine):
            return
        cookies = self.tracker.get_cookies()
        with DBSession() as db:
            db_series = db.query(LostFilmTVSeries).all()
            series = map(row2dict, db_series)
        series_names = {s[u'search_name'].lower(): s for s in series}
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
                if not filename:
                    filename = original_name
                torrent = Torrent(torrent_content)
                engine.log.downloaded(u'Download new series: {0} ({1})'
                                      .format(original_name, info['episode_info']),
                                      torrent_content)
                last_update = engine.add_torrent(filename, torrent, None)
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

    def get_topic_info(self, topic):
        if topic.season and topic.episode:
            return "S%02dE%02d" % (topic.season, topic.episode)
        if topic.season:
            return "S%02d" % topic.season
        return None

    def _prepare_request(self, topic):
        # this method shouldn't be called for lostfilm plugin
        raise NotImplementedError

    def _get_display_name(self, parsed_url):
        if 'name' in parsed_url:
            return u"{0} / {1}".format(parsed_url['name'], parsed_url['original_name'])
        return parsed_url['original_name']

    def _set_topic_params(self, url, parsed_url, topic, params):
        """
        :param url: str
        :type topic: LostFilmTVSeries
        """
        super(TrackerPluginWithCredentialsBase, self)._set_topic_params(url, parsed_url, topic, params)
        if parsed_url is not None:
            topic.search_name = parsed_url['original_name']

register_plugin('tracker', PLUGIN_NAME, LostFilmPlugin(), upgrade=upgrade)
