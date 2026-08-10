#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import six
from requests import Session
import requests
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from monitorrent.db import Base, DBSession
from monitorrent.plugins import Topic
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, \
    LoginResult, TrackerSettings, update_headers_and_cookies_mixin

PLUGIN_NAME = 'rutracker.org'

# Cloudflare lets a request through when it has cf_clearance plus the
# User-Agent that cookie was issued for. Both fields take a single value copied
# from a browser, or a json object like lostfilm's.


def _parse_json_or_value(value, key):
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith('{'):
        return json.loads(value)
    return {key: value}


def parse_cookies_field(value):
    """bare cf_clearance value, or a json object of cookies"""
    return _parse_json_or_value(value, 'cf_clearance')


def parse_headers_field(value):
    """bare User-Agent, or a json object of headers

    no default on purpose: a made up agent would not match cf_clearance
    """
    return _parse_json_or_value(value, 'User-Agent')


class RutrackerCredentials(Base):
    __tablename__ = "rutracker_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    uid = Column(String, nullable=True)
    bb_data = Column(String, nullable=True)
    cookies = Column(String, nullable=True)
    headers = Column(String, nullable=True)


class RutrackerTopic(Topic):
    __tablename__ = "rutracker_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class RutrackerLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), RutrackerTopic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        with operations_factory() as operations:
            cookies_column = Column('cookies', String, nullable=True)
            headers_column = Column('headers', String, nullable=True)
            operations.add_column(RutrackerCredentials.__tablename__, cookies_column)
            operations.add_column(RutrackerCredentials.__tablename__, headers_column)
        version = 1


def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(RutrackerTopic.__tablename__, m, autoload=True)
    credentials = Table(RutrackerCredentials.__tablename__, m, autoload=True)
    if 'cookies' not in credentials.columns:
        return 0
    return 1


class RutrackerTracker(object):
    tracker_settings: TrackerSettings = None
    login_url = "https://rutracker.org/forum/login.php"
    profile_page = "https://rutracker.org/forum/privmsg.php?folder=inbox"
    _regex = re.compile(six.text_type(r'^https?://w*\.*rutracker.org/forum/viewtopic.php\?t=(\d+)(/.*)?$'))
    uid_regex = re.compile(six.text_type(r'\d*-(\d*)-.*'))

    def __init__(self, headers_cookies_updater=lambda h, c: None, uid=None, bb_data=None, headers=None, cookies=None):
        self.uid = uid
        self.bb_data = bb_data
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.headers_cookies_updater = headers_cookies_updater

    def setup(self, uid, bb_data, headers=None, cookies=None):
        self.uid = uid
        self.bb_data = bb_data
        self.headers = headers or {}
        self.cookies = cookies or {}

    def can_parse_url(self, url):
        return self._regex.match(url) is not None

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())

        soup = get_soup(r.text)
        if soup.h1 is None:
            # rutracker doesn't return 404 for not existing topic
            # it return regular page with text 'Тема не найдена'
            # and we can check it by not existing heading of the requested topic
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def login(self, username, password, headers=None, cookies=None):
        self.headers = headers
        self.cookies = cookies
        # probe login.php, not the index: the index is not behind the challenge,
        # so probing it always reports "no protection" and never solves anything
        headers, cookies = update_headers_and_cookies_mixin(self, self.login_url)

        username_q = username.encode('windows-1251')
        password_q = password.encode('windows-1251')
        data = {"login_username": username_q, "login_password": password_q, 'login': u'%E2%F5%EE%E4'}

        s = Session()
        kwargs = {}
        if self.tracker_settings:
            kwargs = self.tracker_settings.get_requests_kwargs()

        login_result = s.post(self.login_url, data, headers=headers, cookies=cookies, **kwargs)

        # the challenge is served from login.php itself, so the url check below
        # would read it as a returned login form and blame the password
        if login_result.status_code == 403:
            raise RutrackerLoginFailedException(3, "Blocked by Cloudflare challenge, not a credentials problem")

        if login_result.url.startswith(self.login_url):
            # TODO get error info (although it shouldn't contain anything useful
            # it can contain request to enter capture, so we should handle it
            raise RutrackerLoginFailedException(1, "Invalid login or password")
        else:
            bb_data = s.cookies.get('bb_session')
            if not bb_data:
                raise RutrackerLoginFailedException(2, "Failed to retrieve cookie")

            self.bb_data = bb_data
            self.uid = self.uid_regex.match(bb_data).group(1)

    def verify(self):
        if not self.uid:
            return False
        cookies = self.get_cookies()
        if not cookies:
            return False
        profile_page_result = requests.get(self.profile_page, cookies=cookies, headers=self.headers,
                                           **self.tracker_settings.get_requests_kwargs())
        # the challenge answers 403 without redirecting, so the url alone says
        # nothing about the session
        return profile_page_result.status_code == 200 and profile_page_result.url == self.profile_page

    def get_cookies(self):
        if not self.bb_data:
            return False
        # cf_clearance has to travel with every request, not just the login
        cookies = dict(self.cookies or {})
        cookies['bb_session'] = self.bb_data
        return cookies

    def get_id(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        return match.group(1)

    # noinspection PyShadowingBuiltins
    def get_download_url(self, url):
        id = self.get_id(url)
        if id is None:
            return None

        return "https://rutracker.org/forum/dl.php?t=" + id


class RutrackerPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = RutrackerTracker()
    topic_class = RutrackerTopic
    credentials_class = RutrackerCredentials
    # whitelists: without cookies and headers the form fields below are dropped
    credentials_public_fields = ['username', 'cookies', 'headers']
    credentials_private_fields = ['username', 'password', 'cookies', 'headers']
    # same escape hatch lostfilm has: the bundled solver cannot pass the current
    # challenge, so a cf_clearance from a real browser is what makes this work
    credentials_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'username',
            'label': 'Username',
            'flex': 50
        }, {
            "type": "password",
            "model": "password",
            "label": "Password",
            "flex": 50
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'cookies',
            'label': 'cf_clearance cookie (DevTools → Application → Cookies)',
            'flex': 100,
        }],
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'headers',
            'label': 'User-Agent of the same browser (navigator.userAgent)',
            'flex': 100,
        }],
    }]
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    def login(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return LoginResult.CredentialsNotSpecified
            username = cred.username
            password = cred.password
            headers = parse_headers_field(cred.headers)
            cookies = parse_cookies_field(cred.cookies)
            if not username or not password:
                return LoginResult.CredentialsNotSpecified
            # cf_clearance is refused with any other User-Agent, so it is the
            # pair or nothing
            if cookies and 'cf_clearance' in cookies and not (headers or {}).get('User-Agent'):
                return LoginResult.CredentialsNotSpecified
        try:
            self.tracker.login(username, password, headers, cookies)
            with DBSession() as db:
                cred = db.query(self.credentials_class).first()
                cred.uid = self.tracker.uid
                cred.bb_data = self.tracker.bb_data
                cred.headers = json.dumps(self.tracker.headers)
                cred.cookies = json.dumps(self.tracker.cookies)
            return LoginResult.Ok
        except RutrackerLoginFailedException as e:
            if e.code == 1:
                return LoginResult.IncorrentLoginPassword
            return LoginResult.Unknown
        except Exception as e:
            # TODO: Log unexpected excepton
            return LoginResult.Unknown

    def verify(self):
        with DBSession() as db:
            cred = db.query(self.credentials_class).first()
            if not cred:
                return False
            username = cred.username
            password = cred.password
            if not username or not password or not cred.uid or not cred.bb_data:
                return False
            # restore cookies and headers too: login() reads them from the db
            # itself, so without this everything after login goes out bare
            self.tracker.setup(cred.uid, cred.bb_data,
                               headers=parse_headers_field(cred.headers),
                               cookies=parse_cookies_field(cred.cookies))
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        # the cookie needs its own User-Agent; request headers still win
        headers = dict(self.tracker.headers or {})
        headers.update({'referer': topic.url, 'host': "rutracker.org"})
        cookies = self.tracker.get_cookies()
        request = requests.Request('POST', self.tracker.get_download_url(topic.url), headers=headers, cookies=cookies)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, RutrackerPlugin(), upgrade=upgrade)
