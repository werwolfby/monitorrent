#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import six
import sys
import pytz
import datetime
from requests import Session
import requests
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData, Table
from monitorrent.db import Base, DBSession, UTCDateTime
from monitorrent.plugins import Topic
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, LoginResult

PLUGIN_NAME = 'kinozal.tv'


class KinozalCredentials(Base):
    __tablename__ = "kinozal_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    c_uid = Column(String, nullable=True)
    c_pass = Column(String, nullable=True)
    domain = Column(String, nullable=True, server_default='kinozal.tv')


class KinozalTopic(Topic):
    __tablename__ = "kinozal_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)
    last_torrent_update = Column(UTCDateTime, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(KinozalTopic.__tablename__, m, autoload=True)
    creds = Table(KinozalCredentials.__tablename__, m, autoload=True)
    if 'last_torrent_update' not in topics.columns:
        return 0
    if 'domain' not in creds.columns:
        return 1
    return 2


def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), KinozalTopic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        with operations_factory() as operations:
            operations.rename_table('Kinozal_topics', 'kinozal_topics1')
            operations.rename_table('kinozal_topics1', KinozalTopic.__tablename__)

            operations.rename_table('Kinozal_credentials', 'kinozal_credentials1')
            operations.rename_table('kinozal_credentials1', KinozalCredentials.__tablename__)

            last_torrent_update = Column('last_torrent_update', UTCDateTime, nullable=True)
            operations.add_column(KinozalTopic.__tablename__, last_torrent_update)
        version = 1
    if version == 1:
        with operations_factory() as operations:
            domain = Column('domain', String, nullable=True, server_default='kinozal.tv')
            operations.add_column(KinozalCredentials.__tablename__, domain)
        version = 2


class KinozalDateParser(object):
    months = {
        u'января': 1,
        u'февраля': 2,
        u'марта': 3,
        u'апреля': 4,
        u'мая': 5,
        u'июня': 6,
        u'июля': 7,
        u'августа': 8,
        u'сентября': 9,
        u'октября': 10,
        u'ноября': 11,
        u'декабря': 12,
    }
    relative_days = {
        u'сегодня': 0,
        u'вчера': -1
    }
    now_text = u'сейчас'
    tz_moscow = pytz.timezone(u'Europe/Moscow')

    def __init__(self):
        months = u'|'.join(self.months)
        relative_days = u'(?P<relative>{0}|{1})'.format(*self.relative_days.keys())
        time_pattern = u'(?P<hours>\d{1,2}):(?P<minutes>\d{1,2})'
        date_pattern = u'(?P<day>\d{1,2})\s+(?P<month>' + months + u')\s+(?P<year>\d{4})'
        pattern = u'^({0}|{1})\s+в\s+{2}$'.format(date_pattern, relative_days, time_pattern)
        self.time_parse_re = re.compile(pattern, re.UNICODE | re.IGNORECASE)

    def parse(self, date_string):
        if self.now_text in date_string:
            return datetime.datetime.now(pytz.utc)

        match = self.time_parse_re.match(date_string)
        if not match:
            raise Exception(u"Can't parse string: {0}".format(date_string))

        parts = match.groupdict()
        if 'relative' in parts and parts['relative'] is not None:
            delta = datetime.timedelta(days=self.relative_days[parts['relative']])
            date = self.tz_moscow.normalize(datetime.datetime.now(pytz.utc) + delta).date()
        else:
            date = datetime.date(int(parts['year']), self.months[parts['month']], int(parts['day']))

        parsed_date_time = datetime.datetime(date.year, date.month, date.day, int(parts['hours']),
                                             int(parts['minutes']))

        return self.tz_moscow.localize(parsed_date_time)


class KinozalLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class KinozalTracker(object):
    tracker_settings = None
    date_parser = KinozalDateParser()
    
    # Регулярка теперь принимает ЛЮБОЙ домен, содержащий kinozal
    url_regex = re.compile(six.text_type(r'^https?://[^/]*kinozal[^/]*/details\.php\?id=(\d+)$'))

    def __init__(self, c_uid=None, c_pass=None, domain='kinozal.tv'):
        self.c_uid = c_uid
        self.c_pass = c_pass
        self.domain = domain or 'kinozal.tv'

    def setup(self, c_uid, c_pass, domain='kinozal.tv'):
        self.c_uid = c_uid
        self.c_pass = c_pass
        self.domain = domain or 'kinozal.tv'

    @property
    def login_url(self):
        return "https://{}/takelogin.php".format(self.domain)

    @property
    def profile_page(self):
        return "https://{}/inbox.php".format(self.domain)

    def can_parse_url(self, url):
        return self.url_regex.match(url) is not None

    def parse_url(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None
        torrent_id = match.group(1)

        real_url = "https://{}/details.php?id={}".format(self.domain, torrent_id)
        
        try:
            r = requests.get(real_url, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())
            r.raise_for_status()
        except requests.exceptions.RequestException:
            return None

        soup = get_soup(r.text)
        if soup.h1 is None:
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def login(self, username, password):
        s = Session()
        data = {"username": username, "password": password, 'returnto': ''}
        
        try:
            login_result = s.post(self.login_url, data, **self.tracker_settings.get_requests_kwargs())
        except requests.exceptions.RequestException:
            raise KinozalLoginFailedException(3, "Connection failed")

        if login_result.url.startswith(self.login_url):
            raise KinozalLoginFailedException(1, "Invalid login or password")
        else:
            c_pass = s.cookies.get('pass')
            c_uid = s.cookies.get('uid')
            if not c_pass or not c_uid:
                raise KinozalLoginFailedException(2, "Failed to retrieve cookie")

            self.c_pass = c_pass
            self.c_uid = c_uid

    def verify(self):
        if not self.c_uid:
            return False
        cookies = self.get_cookies()
        if not cookies:
            return False
            
        try:
            profile_page_result = requests.get(self.profile_page, cookies=cookies,
                                               **self.tracker_settings.get_requests_kwargs())
            return profile_page_result.url == self.profile_page
        except requests.exceptions.RequestException:
            return False

    def get_cookies(self):
        if not self.c_pass or not self.c_uid:
            return False
        return {'pass': self.c_pass, 'uid': self.c_uid}

    def get_id(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None
        return match.group(1)

    def get_last_torrent_update(self, url):
        torrent_id = self.get_id(url)
        if torrent_id is None:
            return None
            
        real_url = "https://{}/details.php?id={}".format(self.domain, torrent_id)
        
        try:
            response = requests.get(real_url, **self.tracker_settings.get_requests_kwargs())
            response.raise_for_status()
        except requests.exceptions.RequestException:
            return None

        soup = get_soup(response.text)
        content = soup.find("div", {"class": "mn1_menu"})
        if content is None:
            return None
            
        text_element = content.find(lambda tag: (tag.name == 'li') and (u'Обновлен' in tag.contents))
        date_text = None
        if text_element is not None:
            text_element = text_element.find("span")
            if text_element is not None:
                date_text = text_element.string
        if date_text is None:
            text_element = content.find(lambda tag: (tag.name == 'li') and (u'Залит' in tag.contents))
            if text_element is not None:
                text_element = text_element.find("span")
                if text_element is not None:
                    date_text = text_element.string
        if date_text is None:
            return None

        parsed_datetime = self.date_parser.parse(date_text)
        return parsed_datetime.astimezone(pytz.utc)

    def get_download_url(self, url):
        torrent_id = self.get_id(url)
        if torrent_id is None:
            return None
        return "https://{}/download.php?id={}".format(self.domain, torrent_id)


class KinozalPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = KinozalTracker()
    topic_class = KinozalTopic
    credentials_class = KinozalCredentials
    
    # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Добавление этих строк заставляет API Monitorrent обрабатывать и сохранять домен[cite: 2]
    credentials_public_fields = ['username', 'domain']
    credentials_private_fields = ['username', 'password', 'domain']

    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    credentials_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'username',
            'label': 'Логин',
            'flex': 50
        }, {
            'type': 'password',
            'model': 'password',
            'label': 'Пароль',
            'flex': 50
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'domain',
            'label': 'Домен (варианты: kinozal.tv, kinozal.guru, kinozal.me)',
            'flex': 100
        }]
    }]

    def _get_domain(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if cred and cred.domain:
                return cred.domain
        return 'kinozal.tv'

    def login(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return LoginResult.CredentialsNotSpecified
            username = cred.username
            password = cred.password
            domain = cred.domain or 'kinozal.tv'
            if not username or not password:
                return LoginResult.CredentialsNotSpecified
        try:
            self.tracker.setup(None, None, domain)
            self.tracker.login(username, password)
            with DBSession() as db:
                cred = db.query(self.credentials_class).first()
                cred.c_uid = self.tracker.c_uid
                cred.c_pass = self.tracker.c_pass
                cred.domain = domain
            return LoginResult.Ok
        except KinozalLoginFailedException as e:
            if e.code == 1:
                return LoginResult.IncorrentLoginPassword
            return LoginResult.Unknown
        except Exception as e:
            return LoginResult.Unknown

    def verify(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return False
            username = cred.username
            password = cred.password
            domain = cred.domain or 'kinozal.tv'
            if not username or not password or not cred.c_uid or not cred.c_pass:
                return False
            self.tracker.setup(cred.c_uid, cred.c_pass, domain)
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        self.tracker.domain = self._get_domain()
        return self.tracker.parse_url(url)

    def check_changes(self, topic):
        self.tracker.domain = self._get_domain()
        last_torrent_update = self.tracker.get_last_torrent_update(topic.url)
        topic_last_torrent_update = topic.last_torrent_update
        min_date = pytz.utc.localize(datetime.datetime.min)

        if (not last_torrent_update and not topic_last_torrent_update) or (topic_last_torrent_update or min_date) < (last_torrent_update or min_date):
            topic.last_torrent_update = last_torrent_update
            return True

        return False

    def _prepare_request(self, topic):
        self.tracker.domain = self._get_domain()
        headers = {'referer': topic.url}
        cookies = self.tracker.get_cookies()
        request = requests.Request('GET', self.tracker.get_download_url(topic.url), headers=headers, cookies=cookies)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, KinozalPlugin(), upgrade)
