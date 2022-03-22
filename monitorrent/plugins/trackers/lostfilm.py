# coding=utf-8
import json
import sys
import re
import requests
import cloudscraper
import traceback
import six
from enum import Enum
from requests import Response
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from monitorrent.db import Base, DBSession, UTCDateTime, row2dict
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.utils.bittorrent_ex import Torrent, is_torrent_content
from monitorrent.utils.downloader import download
from monitorrent.plugins import Topic
from monitorrent.plugins.status import Status
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, LoginResult, \
    CloudflareCookiesExtractor
from monitorrent.plugins.clients import TopicSettings
import html

PLUGIN_NAME = 'lostfilm.tv'

scraper = cloudscraper.create_scraper()


class LostFilmTVSeries(Topic):
    __tablename__ = "lostfilmtv_series"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    cat = Column(Integer, nullable=False)
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
    session = Column(String, nullable=True)
    cookies = Column(String, nullable=True)
    headers = Column(String, nullable=True)
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
    if version == 3:
        upgrade_3_to_4(engine, operations_factory)
        version = 4
    if version == 4:
        with operations_factory() as operations:
            cookies_column = Column('cookies', String, nullable=True)
            headers_column = Column('headers', String, nullable=True)
            operations.add_column(LostFilmTVCredentials.__tablename__, cookies_column)
            operations.add_column(LostFilmTVCredentials.__tablename__, headers_column)
        version = 5


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
    if 'cat' not in topics.columns:
        return 3
    if 'cookies' not in credentials.columns:
        return 4
    return 5


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


def upgrade_3_to_4(engine, operations_factory):
    # Version 3
    m3 = MetaData()
    lostfilm_series_3 = Table('lostfilmtv_series', m3,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("search_name", String, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))
    lostfilm_credentials_3 = Table("lostfilmtv_credentials", m3,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('uid', String),
                                   Column('pass', String),
                                   Column('usess', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))

    # Version 4
    m4 = MetaData(engine)
    topic_last = Table('topics', m4, *[c.copy() for c in Topic.__table__.columns])
    lostfilm_series_4 = Table('lostfilmtv_series4', m4,
                              Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                              Column("cat", Integer, nullable=False),
                              Column("season", Integer, nullable=True),
                              Column("episode", Integer, nullable=True),
                              Column("quality", String, nullable=False))
    lostfilm_credentials_4 = Table("lostfilmtv_credentials4", m4,
                                   Column('username', String, primary_key=True),
                                   Column('password', String, primary_key=True),
                                   Column('session', String),
                                   Column('default_quality', String, nullable=False, server_default='SD'))

    cat_re = re.compile(six.text_type(r'https?://(www|old)\.lostfilm\.tv/browse\.php\?cat=_?(?P<cat>\d+)'), re.UNICODE)

    from monitorrent.settings_manager import SettingsManager
    settings_manager = SettingsManager()

    tracker_settings = None

    with operations_factory() as operations:
        # if previuos run fails, it can not delete this table
        if operations.has_table(lostfilm_series_4.name):
            operations.drop_table(lostfilm_series_4.name)
        operations.create_table(lostfilm_series_4)

        lostfilm_topics = operations.db.query(lostfilm_series_3)
        topics = operations.db.query(topic_last)
        topics = [row2dict(t, topic_last) for t in topics]
        topics = {t['id']: t for t in topics}
        for topic in lostfilm_topics:
            raw_lostfilm_topic = row2dict(topic, lostfilm_series_3)
            raw_topic = topics[raw_lostfilm_topic['id']]
            match = cat_re.match(raw_topic['url'])

            topic_values = {}

            if not match:
                print("can't parse old url: {0}".format(raw_topic['url']))
                raw_lostfilm_topic['cat'] = 0
                topic_values['status'] = Status.Error
            else:
                cat = int(match.group('cat'))
                raw_lostfilm_topic['cat'] = cat

                try:
                    if tracker_settings is None:
                        tracker_settings = settings_manager.tracker_settings

                    old_url = 'https://www.lostfilm.tv/browse.php?cat={0}'.format(cat)
                    url_response = scraper.get(old_url, **tracker_settings.get_requests_kwargs())

                    soup = get_soup(url_response.text)
                    meta_content = soup.find('meta').attrs['content']
                    redirect_url = meta_content.split(';')[1].strip()[4:]

                    if redirect_url.startswith('/'):
                        redirect_url = redirect_url[1:]

                    redirect_url = u'https://www.lostfilm.tv/{0}'.format(redirect_url)
                    url = LostFilmShow.get_seasons_url(redirect_url)

                    if url is None:
                        raise Exception("Can't parse url from {0} it was redirected to {1}"
                                        .format(old_url, redirect_url))

                    topic_values['url'] = url
                except:
                    exc_info = sys.exc_info()
                    print(u''.join(traceback.format_exception(*exc_info)))
                    topic_values['status'] = Status.Error

            operations.db.execute(lostfilm_series_4.insert(), raw_lostfilm_topic)
            operations.db.execute(topic_last.update(whereclause=(topic_last.c.id == raw_topic['id']),
                                                    values=topic_values))

        # drop original table
        operations.drop_table(lostfilm_series_3.name)
        # rename new created table to old one
        operations.rename_table(lostfilm_series_4.name, lostfilm_series_3.name)

        # if previuos run fails, it can not delete this table
        if operations.has_table(lostfilm_credentials_4.name):
            operations.drop_table(lostfilm_credentials_4.name)
        operations.create_table(lostfilm_credentials_4)
        credentials = list(operations.db.query(lostfilm_credentials_3))
        for credential in credentials:
            raw_credential = row2dict(credential, lostfilm_credentials_3)
            operations.db.execute(lostfilm_credentials_4.insert(), raw_credential)

        # drop original table
        operations.drop_table(lostfilm_credentials_3.name)
        # rename new created table to old one
        operations.rename_table(lostfilm_credentials_4.name, lostfilm_credentials_3.name)


class LostFilmTVException(Exception):
    pass


class LostFilmTVLoginFailedException(Exception):
    def __init__(self, code):
        self.code = code


class SpecialSeasons(Enum):
    Unknown = 9999   # 999 is used for Additional for most cases
    Additional = 1

    @classmethod
    def is_special(cls, number):
        return isinstance(number, cls)


class LostFilmEpisode(object):
    """
        :type season: int | tuple[int, int] | SpecialSeasons
        :type number: int

    """
    def __init__(self, season, number):
        self.season = season
        self.number = number

    def is_special_season(self):
        return SpecialSeasons.is_special(self.season)


class LostFilmSeason(object):
    """

        :type number: int | tuple[int, int] | SpecialSeasons
        :type episodes: list[LostFilmEpisode]
        :type episodes_dict: dict[int, LostFilmSeason]

    """
    def __init__(self, number):
        """
        :type number: int | tuple[int, int] | SpecialSeasons
        """
        if not isinstance(number, (int, SpecialSeasons)) and \
            not (isinstance(number, tuple) and len(number) == 2 and
                 isinstance(number[0], int) and isinstance(number[1], int)):
            raise Exception("Season number can be: int, tuple[int, int] or SpecialSeason, but was {0}"
                            .format(type(number)))

        self.number = number
        self.episodes = []
        self.episodes_dict = {}

    def add_episode(self, episode):
        """
        :type episode: LostFilmEpisode
        """
        if episode.number in self.episodes_dict:
            raise Exception("Episode {0} already exists in the season {1}".format(episode.number, self.number))

        self.episodes.append(episode)
        self.episodes.sort(key=lambda s: s.number, reverse=True)

        self.episodes_dict[episode.number] = episode

    def is_special_season(self):
        return SpecialSeasons.is_special(self.number)

    @property
    def last_episode(self):
        return self.episodes[0] if len(self.episodes) > 0 else None

    def __len__(self):
        return len(self.episodes)

    def __getitem__(self, number):
        """
        :rtype: LostFilmEpisode
        """
        return self.episodes_dict[number]

    def __iter__(self):
        """
        :rtype: list[LostFilmEpisode]
        """
        return reversed(self.episodes)

    def __reversed__(self):
        """
        :rtype: list[LostFilmEpisode]
        """
        return iter(self.episodes)


class LostFilmShow(object):
    _regex = re.compile(six.text_type(r'^https?://www\.lostfilm\.tv/series/(?P<name>[^/]+)(.*)$'))

    """

        :type original_name: unicode
        :type russian_name: unicode
        :type url_name: unicode
        :type cat: int
        :type seasons: list[LostFilmSeason]
        :type seasons_dict: dict[int, LostFilmSeason]

    """
    def __init__(self, original_name, russian_name, url_name, cat):
        """
        """
        self.original_name = original_name
        self.russian_name = russian_name
        self.url_name = url_name
        self.cat = cat
        self.seasons = []
        self.seasons_dict = {}

    def add_season(self, season):
        """
        :type season: LostFilmSeason
        """
        if season.number in self.seasons_dict:
            raise Exception("Season {0} already added to show".format(season.number))

        self.seasons.append(season)
        self.seasons.sort(key=lambda s: 999 if SpecialSeasons.is_special(s.number) else s.number, reverse=True)

        self.seasons_dict[season.number] = season

    @property
    def seasons_url(self):
        return'https://www.lostfilm.tv/series/{0}/seasons'.format(self.url_name)

    @property
    def last_season(self):
        for season in self.seasons:
            if not season.is_special_season():
                return season

        return None

    @staticmethod
    def get_seasons_url(url):
        return LostFilmShow.get_seasons_url_info(url)[1]

    @staticmethod
    def get_seasons_url_info(url):
        match = LostFilmShow._regex.match(url)
        if not match:
            return None, None
        name = match.group('name')
        return name, 'https://www.lostfilm.tv/series/{0}/seasons'.format(name)

    def __len__(self):
        return len(self.seasons)

    def __getitem__(self, number):
        return self.seasons_dict[number]

    def __iter__(self):
        """
        :rtype: list[LostFilmSeason]
        """
        return reversed(self.seasons)

    def __reversed__(self):
        """
        :rtype: list[LostFilmSeason]
        """
        return iter(self.seasons)


class LostFilmQuality(Enum):
    Unknown = -1,
    SD = 1,
    HD = 2,
    FullHD = 3

    @staticmethod
    def parse(quality):
        quality = quality.lower() if quality is not None else None
        if not quality or quality == 'sd':
            return LostFilmQuality.SD
        if quality == 'mp4' or quality == 'hd' or quality == '720p' or quality == '720':
            return LostFilmQuality.HD
        if quality == '1080p' or quality == '1080':
            return LostFilmQuality.FullHD
        return LostFilmQuality.Unknown


class LostFileDownloadInfo(object):
    """

        :type quality: LostFilmQuality
        :type download_url: unicode

    """
    def __init__(self, quality, download_url):
        """
        :type quality: LostFilmQuality
        :type download_url: unicode
        """
        self.quality = quality
        self.download_url = download_url


class LostFilmTVTracker(object):
    tracker_settings = None
    _season_title_info = re.compile(u'^(?P<season>\d+)(\.(?P<season_fraction>\d+))?\s+сезон' +
                                    u'(\s+((\d+)-)?(?P<episode>\d+)\s+серия)?$')
    _follow_show_re = re.compile(r'^FollowSerial\((?P<cat>\d+)\)$', re.UNICODE)
    _play_episode_re = re.compile(r"^PlayEpisode\('(?P<cat>\d{1,3})\s*(?P<season>\d{3})\s*(?P<episode>\d{3})'\)$",
                                  re.UNICODE)
    _login_cookies_extractor = CloudflareCookiesExtractor('https://www.lostfilm.tv')

    login_url = "https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F"
    profile_url = 'https://www.lostfilm.tv/my.php'
    download_url_pattern = 'https://www.lostfilm.tv/v_search.php?a={cat}{season:03d}{episode:03d}'
    netloc = 'www.lostfilm.tv'

    def __init__(self, session=None, headers=None, cookies=None):
        self.session = session
        self.headers = headers or {}
        self.cookies = cookies or {}

    def setup(self, session=None, headers=None, cookies=None):
        self.session = session
        self.headers = headers or {}
        self.cookies = cookies or {}

    def login(self, email, password, headers=None, cookies=None):
        headers, cookies = self._login_cookies_extractor.extract_credentials(headers or {}, cookies or {})

        params = {"act": "users", "type": "login", "mail": email, "pass": password, "rem": 1, "need_captcha": "", "captcha": ""}
        response = scraper.post("https://www.lostfilm.tv/ajaxik.php", params, headers=headers, cookies=cookies)

        result = response.json()
        if 'error' in result:
            raise LostFilmTVLoginFailedException(result['error'])
        if 'need_captcha' in result:
            raise LostFilmTVLoginFailedException('Captcha requested. Nothing can do about it for now, sorry :(')

        self.setup(response.cookies['lf_session'], headers, cookies)

    def verify(self):
        cookies = self.get_cookies()
        if not cookies:
            return False
        my_settings_url = 'https://www.lostfilm.tv/my_settings'
        r1 = scraper.get(my_settings_url, headers=self.headers, cookies=cookies,
                         **self.tracker_settings.get_requests_kwargs())
        return r1.url == my_settings_url and '<meta http-equiv="refresh" content="0; url=/">' not in r1.text

    def get_cookies(self):
        if not self.session:
            return False
        new_cookies = dict(**self.cookies)
        new_cookies.update({'lf_session': self.session})
        return new_cookies

    def can_parse_url(self, url):
        return LostFilmShow.get_seasons_url(url) is not None

    def parse_url(self, url, parse_series=False):
        """
        :rtype: requests.Response | LostFilmShow
        """
        name, url = LostFilmShow.get_seasons_url_info(url)
        if url is None:
            return None

        headers, cookies = self._update_headers_and_cookies()

        response = scraper.get(url, headers=headers, cookies=cookies, allow_redirects=False,
                               **self.tracker_settings.get_requests_kwargs())
        if response.status_code != 200 or response.url != url \
                or '<meta http-equiv="refresh" content="0; url=/">' in response.text:
            return response
        # lxml have some issue with parsing lostfilm on Windows, so replace it on html5lib for Windows
        soup = get_soup(response.text, 'html5lib' if sys.platform == 'win32' else None)
        title_block = soup.find('div', class_='title-block')
        follow_show = title_block.find('div', onclick=self._follow_show_re).attrs['onclick']
        follow_show_match = self._follow_show_re.match(follow_show)

        result = LostFilmShow(original_name=title_block.find('h2', class_='title-en').text,
                              russian_name=title_block.find('h1', class_='title-ru').text,
                              url_name=name,
                              cat=int(follow_show_match.group('cat')))
        if parse_series:
            for season in self._parse_series(soup):
                result.add_season(season)
        return result

    def _parse_series(self, soup):
        """
        :rtype : dict
        """
        series_block = soup.find('div', class_='series-block')
        serie_blocks = series_block.find_all('div', class_='serie-block')
        result = dict()
        for season_node in serie_blocks:
            season_title = season_node.find('h2').text
            series_table = season_node.find('table', class_='movie-parts-list')
            series = series_table.find_all('tr', class_=None)

            # when next season is planned it already exist on seasons page
            # but without any episodes yet and without download button
            if not any(series):
                continue

            season_number = self._parse_season_info(season_title)

            season = LostFilmSeason(season_number)
            for serie in series:
                zeta = serie.find('td', class_='zeta')
                play_episode = zeta.find('div').attrs['onclick']

                play_episode_match = self._play_episode_re.match(play_episode)
                episode_number = int(play_episode_match.group('episode'))

                episode = LostFilmEpisode(season_number, episode_number)
                season.add_episode(episode)
            yield season

    def _parse_season_info(self, info):
        if info == u'Дополнительные материалы':
            return SpecialSeasons.Additional
        match = self._season_title_info.match(info)
        if not match:
            return SpecialSeasons.Unknown
        season = int(match.group('season'))
        episode = int(match.group('episode')) if match.group('episode') else None
        if episode is None:
            return season
        return season, episode

    def get_download_info(self, url, cat, season, episode):
        if LostFilmShow.get_seasons_url(url) is None:
            return None

        def parse_download(table):
            quality = table.find('div', class_="inner-box--label").text.strip()
            download_url = table.find('a').attrs['href']

            return LostFileDownloadInfo(LostFilmQuality.parse(quality), download_url)

        headers, cookies = self._update_headers_and_cookies()

        download_redirect_url = self.download_url_pattern.format(cat=cat, season=season, episode=episode)
        download_redirect = scraper.get(download_redirect_url, headers=headers, cookies=cookies,
                                        **self.tracker_settings.get_requests_kwargs())

        soup = get_soup(download_redirect.text)
        meta_content = soup.find('meta').attrs['content']
        download_page_url = meta_content.split(';')[1].strip()[4:]

        download_page = scraper.get(download_page_url, headers=headers, cookies=cookies,
                                    **self.tracker_settings.get_requests_kwargs())

        soup = get_soup(download_page.text)
        return list(map(parse_download, soup.find_all('div', class_='inner-box--item')))

    def _update_headers_and_cookies(self):
        headers, cookies = self._login_cookies_extractor.extract_credentials(self.headers, self.get_cookies())
        # TODO: update headers, cookies in DB if it was changed

        return headers, cookies


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
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'status', 'season', 'episode', 'quality']
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
        result = self.tracker.parse_url(url)
        if isinstance(result, Response):
            return None
        return result

    def prepare_add_topic(self, url):
        parsed_url = self.tracker.parse_url(url)
        if parsed_url is None or isinstance(parsed_url, Response):
            return None
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            quality = cred.default_quality if cred else 'SD'
        settings = {
            'display_name': self._get_display_name(parsed_url),
            'quality': quality
        }

        return settings

    def get_thumbnail_url(self, dbtopic):
        return "https://static.lostfilm.tv/Images/{0}/Posters/icon.jpg".format(dbtopic.cat)

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
                cred.session = self.tracker.session
                cred.headers = json.dumps(self.tracker.headers)
                cred.cookies = json.dumps(self.tracker.cookies)
            return LoginResult.Ok
        except LostFilmTVLoginFailedException as e:
            if e.code == 3:
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
            if not username or not password or not cred.session:
                return False
            self.tracker.setup(cred.session)
        return self.tracker.verify()

    def execute(self, topics, engine):
        """
        :param topics: result of get_topics func
        :type engine: engine.EngineTracker
        :rtype: None
        """
        if not self._execute_login(engine):
            return

        with engine.start(len(topics)) as engine_topics:
            for i in range(0, len(topics)):
                topic = topics[i]
                display_name = topic.display_name
                with engine_topics.start(i, display_name) as engine_topic:
                    episodes = self._prepare_request(topic)
                    status = Status.Ok
                    if isinstance(episodes, Response):
                        status = self.check_download(episodes)

                    if topic.status != status:
                        self.save_topic(topic, None, status)
                        engine_topic.status_changed(topic.status, status)

                    if status != Status.Ok:
                        continue

                    if episodes is None or len(episodes) == 0:
                        engine_topic.info(u"Series <b>{0}</b> not changed".format(display_name))
                        continue

                    with engine_topic.start(len(episodes)) as engine_downloads:
                        for e in range(0, len(episodes)):
                            info, download_info = episodes[e]

                            if download_info is None:
                                engine_downloads.failed(u'Failed get quality "{0}" for series: {1}'
                                                        .format(topic.quality, html.escape(display_name)))
                                # Should fail to get quality be treated as NotFound?
                                self.save_topic(topic, None, Status.Error)
                                break

                            try:
                                response, filename = download(download_info.download_url,
                                                              **self.tracker_settings.get_requests_kwargs())
                                if response.status_code != 200:
                                    raise Exception(u"Can't download url. Status: {}".format(response.status_code))
                            except Exception as e:
                                engine_downloads.failed(u"Failed to download from <b>{0}</b>.\nReason: {1}"
                                                        .format(download_info.download_url, html.escape(str(e))))
                                self.save_topic(topic, None, Status.Error)
                                continue
                            if not filename:
                                filename = display_name
                            torrent_content = response.content
                            if not is_torrent_content(torrent_content):
                                headers = ['{0}: {1}'.format(k, v) for k, v in six.iteritems(response.headers)]
                                engine.failed(u'Downloaded content is not a torrent file.<br>\r\n'
                                              u'Headers:<br>\r\n{0}'.format(u'<br>\r\n'.join(headers)))
                                continue
                            torrent = Torrent(torrent_content)
                            topic.season = info.season
                            topic.episode = info.number
                            last_update = engine_downloads.add_torrent(e, filename, torrent, None,
                                                                       TopicSettings.from_topic(topic))
                            engine_downloads.downloaded(u'Download new series: {0} ({1}, {2})'
                                                        .format(display_name, info.season, info.number),
                                                        torrent_content)
                            self.save_topic(topic, last_update, Status.Ok)

    def get_topic_info(self, topic):
        if topic.season and topic.episode:
            return "S%02dE%02d" % (topic.season, topic.episode)
        if topic.season:
            return "S%02d" % topic.season
        return None

    def _prepare_request(self, topic):
        show = self.tracker.parse_url(topic.url, True)
        if isinstance(show, Response):
            return show
        latest_episode = (topic.season, topic.episode)
        if latest_episode == (None, None):
            episodes = [show.last_season.last_episode]
        else:
            episodes = [episode for season in show for episode in season
                        if not SpecialSeasons.is_special(episode.season) and
                        (episode.season, episode.number) > latest_episode]

        resut = []

        for episode in episodes:
            download_infos = self.tracker.get_download_info(topic.url, topic.cat, episode.season, episode.number)

            topic_quality = LostFilmQuality.parse(topic.quality)
            download_info = None
            if download_infos is not None:
                for test_download_info in download_infos:
                    if test_download_info.quality == topic_quality:
                        download_info = test_download_info
                        break

            resut.append((episode, download_info))

        return resut

    def check_download(self, response):
        if response.status_code == 200:
            if '<meta http-equiv="refresh" content="0; url=/">' in response.text:
                return Status.NotFound
            return Status.Ok

        if response.status_code == 302 and response.headers.get('location', '') == '/':
            return Status.NotFound

        return Status.Error

    def _get_display_name(self, show):
        """
        :type show: LostFilmShow
        """
        if show.russian_name is not None and show.russian_name != '':
            return u"{0} / {1}".format(show.russian_name, show.original_name)
        return show.original_name

    def _set_topic_params(self, url, parsed_url, topic, params):
        """
        :type url: unicde
        :type parsed_url: LostFilmShow
        :type topic: LostFilmTVSeries
        """
        super(LostFilmPlugin, self)._set_topic_params(url, parsed_url, topic, params)
        if parsed_url is not None:
            topic.url = parsed_url.seasons_url
            topic.cat = parsed_url.cat


register_plugin('tracker', PLUGIN_NAME, LostFilmPlugin(), upgrade=upgrade)
