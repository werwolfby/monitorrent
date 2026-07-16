# coding=utf-8
import json
import sys
import re
from urllib.parse import urlparse, urljoin
import requests
import traceback
import six
from enum import Enum
from requests import Response
from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.utils.bittorrent_ex import Torrent, is_torrent_content
from monitorrent.utils.downloader import download
from monitorrent.plugins import Topic
from monitorrent.plugins.status import Status
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, LoginResult, TrackerSettings, \
    update_headers_and_cookies_mixin
from monitorrent.plugins.clients import TopicSettings
import html

PLUGIN_NAME = 'lostfilm.tv'


class LostFilmTVSeries(Topic):
    __tablename__ = "lostfilmtv_series"
    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    cat = Column(Integer, nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    quality = Column(String, nullable=False, server_default='SD')
    __mapper_args__ = {'polymorphic_identity': PLUGIN_NAME}


class LostFilmTVCredentials(Base):
    __tablename__ = "lostfilmtv_credentials"
    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    session = Column(String, nullable=True)
    cookies = Column(String, nullable=True)
    headers = Column(String, nullable=True)
    domain = Column(String, nullable=True, server_default='www.lostfilm.tv')
    default_quality = Column(String, nullable=False, server_default='SD')


def upgrade(engine, operations_factory):
    pass


class LostFilmTVException(Exception): pass
class LostFilmTVLoginFailedException(Exception):
    def __init__(self, code): self.code = code


class SpecialSeasons(Enum):
    Unknown = 9999; Additional = 1


class LostFilmEpisode(object):
    def __init__(self, season_number, episode_number):
        self.season = season_number
        self.number = episode_number


class LostFilmSeason(object):
    def __init__(self, number):
        self.number = number; self.episodes = []
    def add_episode(self, episode):
        if not any(e.number == episode.number for e in self.episodes):
            self.episodes.append(episode)
            self.episodes.sort(key=lambda e: e.number, reverse=True)
    @property
    def last_episode(self): return self.episodes[0] if self.episodes else None
    def __len__(self): return len(self.episodes)


class LostFilmShow(object):
    _regex = re.compile(six.text_type(r'^https?://[^/]*lostfilm.+/series/(?P<name>[^/]+)(.*)$'))
    def __init__(self, original_name, russian_name, url_name, cat):
        self.original_name = original_name; self.russian_name = russian_name
        self.url_name = url_name; self.cat = cat; self.seasons = []
    def add_season(self, season):
        if not any(s.number == season.number for s in self.seasons):
            self.seasons.append(season)
            self.seasons.sort(key=lambda s: 999 if isinstance(s.number, SpecialSeasons) else s.number, reverse=True)
    @property
    def last_season(self):
        for s in self.seasons:
            if not isinstance(s.number, SpecialSeasons): return s
        return None
    @staticmethod
    def get_seasons_url_info(url):
        match = LostFilmShow._regex.match(url)
        return match.group('name') if match else None


class LostFilmQuality(Enum):
    Unknown = -1; SD = 1; HD = 2; FullHD = 3
    @staticmethod
    def parse(quality):
        q = (quality or '').lower()
        if q in ('mp4', 'hd', '720p', '720'): return LostFilmQuality.HD
        if q in ('1080p', '1080'): return LostFilmQuality.FullHD
        return LostFilmQuality.SD


class LostFileDownloadInfo(object):
    def __init__(self, quality, download_url):
        self.quality = quality; self.download_url = download_url


class LostFilmPlugin(WithCredentialsMixin, TrackerPluginBase):
    credentials_class = LostFilmTVCredentials
    topic_class = LostFilmTVSeries

    # Фикс для кавычек и пробелов в JS-вызовах
    _season_title_info = re.compile(u'^(?P<season>\d+)\s+сезон')
    _follow_show_re = re.compile(r'FollowSerial\(\s*[\'"]?(?P<cat>\d+)[\'"]?')
    _play_episode_re = re.compile(r'PlayEpisode\(\s*[\'"](?P<cat>\d{1,4})(?:\s*(?P<season>\d{3})\s*(?P<episode>\d{3})|(?P<combined>\d{6}))[\'"]\)')
#    _season_title_info = re.compile(u'^(?P<season>\d+)\s+сезон')
#    _follow_show_re = re.compile(r'FollowSerial\((?P<cat>\d+)')
#    _play_episode_re = re.compile(r"PlayEpisode\('(?P<cat>\d{1,4})(?:\s*(?P<season>\d{3})\s*(?P<episode>\d{3})|(?P<combined>\d{6}))'\)")

    credentials_public_fields = ['username', 'default_quality', 'cookies', 'headers', 'domain']
    credentials_private_fields = ['username', 'password', 'default_quality', 'cookies', 'headers', 'domain']
    credentials_form = [{'type': 'row', 'content': [{'type': 'text', 'model': 'username', 'label': 'Username', 'flex': 45}, {"type": "password", "model": "password", "label": "Password", "flex": 45}, {"type": "select", "model": "default_quality", "label": "Default Quality", "options": ["SD", "720p", "1080p"], "flex": 10}]}, {'type': 'row', 'content': [{"type": "text", "model": "domain", "label": "Domain, you can specify any www.lostfilm.tv mirror, e.g. www.lostfilmtv.site", "flex": 100}]}, {'type': 'row', 'content': [{'type': 'text', 'model': 'cookies', 'label': 'Cloudflare Cookies, please copy cf_clearance cookie from browser, and paste it here as json:<br>{"cf_clearance": "xxxx-cookies-xxxx"}', 'flex': 100}]}, {'type': 'row', 'content': [{'type': 'text', 'model': 'headers', 'label': 'Headers, please copy User-Agent from browser, and paste it here as json:<br>{"User-Agent": "Mozilla/5.0 (X11; Linux aarch64; rv:99.0) Gecko/20100101 Firefox/99.0"}', 'flex': 100}]}]
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'status', 'season', 'episode', 'quality']
    topic_private_fields = ['display_name', 'season', 'episode', 'quality']
    topic_form = [{'type': 'row', 'content': [{'type': 'text', 'model': 'display_name', 'label': 'Name', 'flex': 70}, {"type": "select", "model": "quality", "label": "Quality", "options": ["SD", "720p", "1080p"], "flex": 30}]}]
    topic_edit_form = [{'type': 'row', 'content': [{'type': 'text', 'model': 'display_name', 'label': 'Name', 'flex': 100}]}, {'type': 'row', 'content': [{'type': 'number', 'model': 'season', 'label': 'Season', 'flex': 40}, {'type': 'number', 'model': 'episode', 'label': 'Episode', 'flex': 40}, {"type": "select", "model": "quality", "label": "Quality", "options": ["SD", "720p", "1080p"], "flex": 20}]}]

    def _create_scraper(self, cred=None):
        scraper = requests.Session()
        if cred:
            try:
                headers = json.loads(cred.headers) if cred.headers else None
                cookies = json.loads(cred.cookies) if cred.cookies else None
            except (TypeError, ValueError):
                headers, cookies = None, None
            if headers: scraper.headers.update(headers)
            if cookies: scraper.cookies.update(cookies)
            if cred.session: scraper.cookies.update({'lf_session': cred.session})
        return scraper

    def login(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred or not cred.username or not cred.password: return LoginResult.CredentialsNotSpecified
            scraper = self._create_scraper(cred)
            domain = cred.domain or 'www.lostfilm.tv'
        try:
            params = {"act": "users", "type": "login", "mail": cred.username, "pass": cred.password, "rem": 1}
            response = scraper.post(f"https://{domain}/ajaxik.users.php", params=params)
            response.raise_for_status()
            result = response.json()
            if 'error' in result: raise LostFilmTVLoginFailedException(result['error'])
            if 'need_captcha' in result: raise LostFilmTVLoginFailedException('Captcha requested')
            with DBSession() as db:
                cred_to_update = db.query(self.credentials_class).first()
                if cred_to_update:
                    cred_to_update.session = scraper.cookies.get('lf_session')
                    cred_to_update.headers = json.dumps(dict(scraper.headers))
                    cred_to_update.cookies = json.dumps(dict(scraper.cookies))
            return LoginResult.Ok
        except Exception: return LoginResult.Unknown

    def verify(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred or not cred.session: return False
            scraper = self._create_scraper(cred)
            domain = cred.domain or 'www.lostfilm.tv'
        my_settings_url = f'https://{domain}/my_settings'
        r = scraper.get(my_settings_url)
        return r.url == my_settings_url and '<meta http-equiv="refresh" content="0; url=/">' not in r.text

    def execute(self, topics, engine):
        if not self._execute_login(engine): return
        with DBSession() as db, engine.start(len(topics)) as engine_topics:
            cred = db.query(self.credentials_class).first()
            if not cred: return
            domain = cred.domain or 'www.lostfilm.tv'
            scraper = self._create_scraper(cred)
            for i, topic in enumerate(topics):
                with engine_topics.start(i, topic.display_name) as engine_topic:
                    try:
                        episodes = self._prepare_request(topic, scraper, domain)
                        if isinstance(episodes, Response):
                             self.save_topic(topic, None, self.check_download(episodes))
                             continue
                        if not episodes:
                            engine_topic.info(f"Series <b>{topic.display_name}</b> not changed")
                            continue
                        with engine_topic.start(len(episodes)) as engine_downloads:
                            for e, (info, download_info) in enumerate(episodes):
                                if download_info is None:
                                    engine_topic.info(f'Quality "{topic.quality}" not available for S{info.season:02d}E{info.number:02d}.')
                                    continue
                                response, filename = download(download_info.download_url, **self.tracker_settings.get_requests_kwargs())
                                torrent_content = response.content
                                if not is_torrent_content(torrent_content):
                                    headers = [f'{k}: {v}' for k, v in six.iteritems(response.headers)]
                                    formatted_headers = "<br>\r\n".join(headers)
                                    engine.failed(f'Downloaded content is not a torrent file.<br>\r\nHeaders:<br>\r\n{formatted_headers}')
                                    continue
                                torrent = Torrent(torrent_content)
                                topic.season, topic.episode = info.season, info.number
                                last_update = engine_downloads.add_torrent(e, filename or topic.display_name, torrent, None, TopicSettings.from_topic(topic))
                                engine_downloads.downloaded(f'New series: {topic.display_name} (S{info.season:02d}E{info.number:02d})', torrent_content)
                                self.save_topic(topic, last_update, Status.Ok)
                    except Exception as ex:
                        engine_topic.failed(f"Exception: {ex}\n{traceback.format_exc()}")
                        self.save_topic(topic, None, Status.Error)

    def _prepare_request(self, topic, scraper, domain):
        show = self._parse_url_logic(topic.url, scraper, domain, True)
        if isinstance(show, Response) or not show: return show
        # Устанавливаем текущие значения, заменяя None на 0 для безопасного сравнения
        current_season = topic.season if topic.season is not None else 0
        current_episode = topic.episode if topic.episode is not None else 0

        # Если это новый торрент без указания сезона, берем только последнюю серию
        if current_season == 0:
            episodes = [show.last_season.last_episode] if show.last_season and show.last_season.last_episode else []
        else:
            # Иначе, ищем все серии, которые вышли после сохраненной
            episodes = [
                ep for s in show.seasons
                for ep in s.episodes
                if not isinstance(s.number, SpecialSeasons) and
                   (s.number > current_season or (s.number == current_season and ep.number > current_episode))
            ]
        
        # Убедимся, что в списке нет значений None, если последней серии не оказалось
        if episodes and episodes[0] is None:
            episodes = []
            
        episodes.reverse()
        result = []
        for episode in episodes:
            infos = self._get_download_info(topic.url, scraper, domain, show.cat, episode.season, episode.number)
            if episode.number == 999:
                continue
            info = next((i for i in infos if i.quality == LostFilmQuality.parse(topic.quality)), None) if infos else None
            result.append((episode, info))
        return result
        
    def can_parse_url(self, url):
        return LostFilmShow.get_seasons_url_info(url) is not None

    def parse_url(self, url):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            scraper = self._create_scraper(cred)
            domain = cred.domain if cred else "www.lostfilm.tv"
        return self._parse_url_logic(url, scraper, domain, False)

    def _parse_url_logic(self, url, scraper, domain, parse_series):
        name = LostFilmShow.get_seasons_url_info(url)
        if not name: return None
        series_url = f'https://{domain}/series/{name}/seasons'
        response, soup = None, None
        try:
            response = scraper.get(series_url, allow_redirects=True, stream=True)
            response.raise_for_status()
            html_content = response.text
        finally:
            if response: response.close()
        soup = get_soup(html_content)
        title_block = soup.find('div', class_='title-block')
        follow_tag = title_block.find('div', onclick=self._follow_show_re) if title_block else None
        if not follow_tag:
            soup.clear(); return None
        match = self._follow_show_re.search(follow_tag['onclick'])
        cat = int(match.group('cat')) if match else 0
        show = LostFilmShow(title_block.find('h2', class_='title-en').text, title_block.find('h1', class_='title-ru').text, name, cat)
        if parse_series:
            for season in self._parse_series(soup): show.add_season(season)
        soup.clear()
        return show

    def _parse_series(self, soup):
        series_block = soup.find('div', class_='series-block')
        if not series_block: return
        for season_node in series_block.find_all(['div', 'section'], class_=['serie-block', 'season', 'season-card']):
            h2 = season_node.find('h2')
            if not h2: continue
            season_number = self._parse_season_info(h2.text.strip())
            season = LostFilmSeason(season_number)
            for element in season_node.find_all('div', onclick=self._play_episode_re):
                match = self._play_episode_re.match(element['onclick'])
                if match:
                    episode_str = match.group('episode') or (match.group('combined') and match.group('combined')[3:])
                    if episode_str:
                        if int(episode_str) == 999: continue
                        episode = LostFilmEpisode(season_number, int(episode_str))
                        season.add_episode(episode)
            if len(season) > 0: yield season

    def _parse_season_info(self, info):
        if 'Дополнительные материалы' in info: return SpecialSeasons.Additional
        match = self._season_title_info.match(info)
        return int(match.group('season')) if match else SpecialSeasons.Unknown

    def _get_download_info(self, url, scraper, domain, cat, season, episode):
        def parse_download(table):
            quality = LostFilmQuality.parse(table.find('div', class_="inner-box--label").text.strip())
            download_url = table.find('a')['href']
            return LostFileDownloadInfo(quality, download_url)
        episode_id = f"{cat}{season:03d}{episode:03d}"
        download_redirect_url = f'https://{domain}/v_search.php?a={episode_id}'
        resp1, resp2 = None, None
        try:
            resp1 = scraper.get(download_redirect_url, stream=True)
            resp1.raise_for_status()
            soup1 = get_soup(resp1.text)
            resp1.close()
            meta = soup1.find('meta', attrs={'http-equiv': 'refresh'})
            if not meta or 'content' not in meta.attrs or ';' not in meta['content']:
                soup1.clear(); return None

            # Извлекаем часть URL из мета-тега
            relative_url = meta['content'].split(';')[1].strip()
            if 'url=' in relative_url.lower():
                relative_url = relative_url.split('url=')[1]

            # Создаем абсолютный URL, используя базовый URL страницы
            base_url = f"https://{domain}/"
            download_page_url = urljoin(base_url, relative_url)

            soup1.clear()
            resp2 = scraper.get(download_page_url, stream=True)
            resp2.raise_for_status()
            soup2 = get_soup(resp2.text)
            result = list(map(parse_download, soup2.find_all('div', class_='inner-box--item')))
            soup2.clear()
            return result
        finally:
            if resp1: resp1.close()
            if resp2: resp2.close()
    
    def prepare_add_topic(self, url):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            # Извлекаем quality до закрытия сессии
            quality = cred.default_quality if cred else 'SD'
            scraper = self._create_scraper(cred)
            domain = cred.domain if cred else "www.lostfilm.tv"
        
        parsed_url = self._parse_url_logic(url, scraper, domain, False)
        
        if parsed_url is None or isinstance(parsed_url, Response): return None
        return {'display_name': self._get_display_name(parsed_url), 'quality': quality}
    
    def _get_display_name(self, show):
        return f"{show.russian_name} / {show.original_name}" if show.russian_name else show.original_name
        
    def get_thumbnail_url(self, topic: LostFilmTVSeries): return f"https://static.lostfilm.top/Images/{topic.cat}/Posters/icon.jpg"
    def get_topic_info(self, topic):
        if topic.season and topic.episode: return f"S{topic.season:02d}E{topic.episode:02d}"
        if topic.season: return f"S{topic.season:02d}"
        return None
    def _set_topic_params(self, url, parsed_url, topic, params):
        super()._set_topic_params(url, parsed_url, topic, params)
        if parsed_url:
            topic.url = f'https://www.lostfilm.tv/series/{parsed_url.url_name}/seasons'
            topic.cat = parsed_url.cat
    def check_download(self, response):
        if response.status_code == 200 and '<meta http-equiv="refresh" content="0; url=/">' in response.text: return Status.NotFound
        if response.status_code == 302 and response.headers.get('location', '') == '/': return Status.NotFound
        return Status.Ok if response.status_code == 200 else Status.Error

register_plugin('tracker', PLUGIN_NAME, LostFilmPlugin(), upgrade=upgrade)
