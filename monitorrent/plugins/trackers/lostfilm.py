# coding=utf-8
import sys
import re
import requests
from bisect import bisect_right
from requests import Session, Response
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from urlparse import urlparse, parse_qs
from monitorrent.db import Base, DBSession, row2dict, UTCDateTime
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.utils.bittorrent import Torrent
from monitorrent.utils.downloader import download
from monitorrent.plugins import Topic, Status
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, LoginResult

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
                              Column('last_update', UTCDateTime, nullable=True),
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
    _regex = re.compile(ur'http://www\.lostfilm\.tv/browse\.php\?cat=(?P<cat>\d+)')
    search_usess_re = re.compile(ur'\(usess=([a-f0-9]{32})\)', re.IGNORECASE)
    _rss_title = re.compile(ur'(?P<name>[^(]+)\s+\((?P<original_name>[^(]+)\)\.\s+' +
                            ur'(?P<title>[^([]+)(\s+\((?P<original_title>[^(]+)\))?' +
                            ur'(\s+\[(?P<quality>[^\]]+)\])?\.\s+' +
                            ur'\((?P<episode_info>[^)]+)\)')
    _season_info = re.compile(ur'S(?P<season>\d{2})(E(?P<episode>\d{2}))+')
    _season_title_info = re.compile(ur'^(?P<season>\d+)(\.(?P<season_fraction>\d+))?\s+сезон'
                                    ur'(\s+((\d+)-)?(?P<episode>\d+)\s+серия)?$')

    login_url = "https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F"
    profile_url = 'http://www.lostfilm.tv/my.php'
    download_url_pattern = 'http://www.lostfilm.tv/nrdr2.php?c={cat}&s={season}&e={episode:02d}'
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
        soup = get_soup(r1.text)
        inputs = soup.findAll("input")
        action = soup.find("form")['action']
        cparams = dict([(i['name'], i['value']) for i in inputs if 'value' in i.attrs])
        r2 = s.post(action, cparams, verify=False, allow_redirects=False)
        if r2.status_code != 302 or r2.headers.get('location', None) != '/':
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

    def parse_url(self, url, parse_series=False):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return r
        parser = None
        # lxml have some issue with parsing lostfilm on Windows
        if sys.platform == 'win32':
            parser = 'html5lib'
        soup = get_soup(r.text, parser)
        title = soup.find('div', class_='mid').find('h1').string
        result = self._parse_title(title)
        result['cat'] = int(match.group('cat'))
        if parse_series:
            result.update(self._parse_series(soup))
        return result

    @staticmethod
    def parse_rss_title(title):
        """
        :type title: str | unicode
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
        quality = quality.lower() if quality is not None else None
        if not quality or quality == 'sd':
            return 'SD'
        if quality == 'mp4' or quality == 'hd' or quality == '720p':
            return '720p'
        if quality == '1080p':
            return '1080p'
        return 'unknown'

    @staticmethod
    def _parse_title(title):
        """
        :type title: unicode
        """
        bracket_index = title.find('(')
        if bracket_index < 0:
            return {'original_name': title}
        name = title[:bracket_index-1].strip()
        original_name = title[bracket_index+1:-1].strip()
        return {'name': name, 'original_name': original_name}

    def _parse_series(self, soup):
        """
        :rtype : dict
        """
        rows = soup.find_all('div', class_='t_row')
        episodes = list()
        complete_seasons = list()
        special_episodes = list()
        special_complete_seasons = list()
        for i, row in enumerate(rows):
            episode_data = self._parse_row(row, i)
            season_info = episode_data['season_info']
            # Complete season: ex: '1 season' -> (1, )
            if len(season_info) == 1:
                complete_seasons.append(episode_data)
            # Complete special season: '2.5 season' -> (2, 5) - like bonues etc.
            elif len(season_info) == 2:
                special_complete_seasons.append(episode_data)
            # Episode for special season: '2.5 season 2 episode' -> (2, 5, 2)
            elif season_info[1] is not None:
                special_episodes.append(episode_data)
            # Regular season episode: '2 season 1 episode' -> (2, None, 1)
            else:
                # Represent regular episode season_info as tuple of (season, episode)
                episode_data['season_info'] = (episode_data['season_info'][0], episode_data['season_info'][2])
                episodes.append(episode_data)
        episodes = sorted(episodes, key=lambda x: x['season_info'])
        complete_seasons = sorted(complete_seasons, key=lambda x: x['season_info'])
        return {
            'episodes': episodes,
            'complete_seasons': complete_seasons,
            'special_episodes': special_episodes,
            'special_complete_seasons': special_complete_seasons
        }

    def _parse_row(self, row, index):
        episode_num = row.find('td', class_='t_episode_num').text.strip()
        season_info = row.find('span', class_='micro').find_all('span')[1].string.strip()
        name = row.find('div', id='TitleDiv' + str(index + 1))
        russian_name = name.find('span').string.strip()
        original_name_item = name.find('br').next_sibling
        if original_name_item is not None:
            original_name = original_name_item.string\
                .strip()\
                .lstrip('(')\
                .rstrip(').')
        else:
            original_name = russian_name

        return {
            'episode_num': episode_num,
            'season_info': self._parse_season_info(season_info),
            'russian_name': russian_name,
            'original_name': original_name
        }

    def _parse_season_info(self, info):
        m = self._season_title_info.match(info)
        season = int(m.group('season'))
        season_fraction = int(m.group('season_fraction')) if m.group('season_fraction') else None
        episode = int(m.group('episode')) if m.group('episode') else None
        if episode is None and season_fraction is None:
            return season,
        if episode is None:
            return season, season_fraction
        return season, season_fraction, episode

    def get_download_info(self, url, season, episode):
        match = self._regex.match(url)

        if match is None:
            return None

        def parse_download(table):
            quality = table.find('img').attrs['src'][11:-4]
            download_url = table.find('a').attrs['href']
            return {
                'quality': self._parse_quality(quality),
                'download_url': download_url
            }

        cat = int(match.group('cat'))

        cookies = self.get_cookies()

        download_redirect_url = self.download_url_pattern.format(cat=cat, season=season, episode=episode)
        download_redirecy = requests.get(download_redirect_url, cookies=cookies)

        soup = get_soup(download_redirecy.text)
        meta_content = soup.find('meta').attrs['content']
        download_page_url = meta_content.split(';')[1].strip()[4:]

        download_page = requests.get(download_page_url)

        soup = get_soup(download_page.text)
        return map(parse_download, soup.find_all('table')[2:])


class LostFilmPlugin(WithCredentialsMixin, TrackerPluginBase):
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
        if not parsed_url or isinstance(parsed_url, Response):
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
        series = self.get_topics(ids)

        for serie in series:
            try:
                display_name = serie.display_name
                episodes = self._prepare_request(serie)
                if isinstance(episodes, Response):
                    status = self.check_download(episodes)
                    if serie.status != status:
                        with DBSession() as db:
                            db.add(serie)
                            serie.status = status
                            db.commit()
                    engine.log.failed(u"Torrent status: %s" % status.__str__())
                    continue

                if episodes is None or len(episodes) == 0:
                    engine.log.info(u"Series <b>{0}</b> not changed".format(display_name))
                    continue

                for episode in episodes:
                    info = episode['season_info']
                    download_info = episode['download_info']

                    if download_info is None:
                        engine.log.failed(u'Failed get quality "{0}" for series: {1}'
                                          .format(serie.quality, display_name))
                        break

                    try:
                        response, filename = download(download_info['download_url'])
                        if response.status_code != 200:
                            raise Exception("Can't download url. Status: {}".format(response.status_code))
                    except Exception as e:
                        engine.log.failed(u"Failed to download from <b>{0}</b>.\nReason: {1}"
                                          .format(download_info['download_url'], e.message))
                        continue
                    if not filename:
                        filename = display_name
                    torrent_content = response.content
                    torrent = Torrent(torrent_content)
                    engine.log.downloaded(u'Download new series: {0} ({1}, {2})'
                                          .format(display_name, info[0], info[1]),
                                          torrent_content)
                    last_update = engine.add_torrent(filename, torrent, None)
                    with DBSession() as db:
                        db_serie = db.query(LostFilmTVSeries)\
                            .filter(LostFilmTVSeries.id == serie.id)\
                            .first()
                        db_serie.last_update = last_update
                        db_serie.season = info[0]
                        db_serie.episode = info[1]
                        db.commit()

            except Exception as e:
                engine.log.failed(u"Failed update <b>lostfilm</b> series: {0}.\nReason: {1}"
                                  .format(serie.search_name, e.message))

    def get_topic_info(self, topic):
        if topic.season and topic.episode:
            return "S%02dE%02d" % (topic.season, topic.episode)
        if topic.season:
            return "S%02d" % topic.season
        return None

    def _prepare_request(self, topic):
        parsed_url = self.tracker.parse_url(topic.url, True)
        if isinstance(parsed_url, Response):
            return parsed_url
        episodes = parsed_url['episodes']
        latest_episode = (topic.season, topic.episode)
        if latest_episode == (None, None):
            not_downloaded_episode_index = -1
        else:
            # noinspection PyTypeChecker
            not_downloaded_episode_index = bisect_right([x['season_info'] for x in episodes], latest_episode)
            if not_downloaded_episode_index >= len(episodes):
                return None

        resut = []

        for episode in episodes[not_downloaded_episode_index:]:
            info = episode['season_info']

            download_infos = self.tracker.get_download_info(topic.url, info[0], info[1])

            download_info = None
            # noinspection PyTypeChecker
            for test_download_info in download_infos:
                if test_download_info['quality'] == topic.quality:
                    download_info = test_download_info
                    break

            resut.append({'season_info': info, 'download_info': download_info})

        return resut

    def check_download(self, response):
        if response.status_code == 200:
            return Status.Ok

        if response.status_code == 302 and response.headers.get('location', '') == '/':
            return Status.NotFound

        return Status.Error

    def _get_display_name(self, parsed_url):
        if 'name' in parsed_url:
            return u"{0} / {1}".format(parsed_url['name'], parsed_url['original_name'])
        return parsed_url['original_name']

    def _set_topic_params(self, url, parsed_url, topic, params):
        """
        :param url: str
        :type topic: LostFilmTVSeries
        """
        super(LostFilmPlugin, self)._set_topic_params(url, parsed_url, topic, params)
        if parsed_url is not None:
            topic.search_name = parsed_url['original_name']

register_plugin('tracker', PLUGIN_NAME, LostFilmPlugin(), upgrade=upgrade)
