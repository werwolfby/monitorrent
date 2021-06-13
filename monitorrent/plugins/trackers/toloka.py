#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import six
from requests import Session
import requests
from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import Base, DBSession
from monitorrent.plugins import Topic
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, LoginResult

PLUGIN_NAME = 'toloka.to'

class TolokaCredentials(Base):
    __tablename__ = "toloka_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    cookies_data = Column(String, nullable=True)

class TolokaTopic(Topic):
    __tablename__ = "toloka_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }

class TolokaLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

class TolokaTracker(object):
    tracker_settings = None
    login_url = "https://toloka.to/login.php"
    profile_page = "https://toloka.to/privmsg.php?folder=inbox"
    _regex = re.compile(six.text_type(r'^https?://toloka.to/[a-z](\d+)$'))

    def __init__(self, cookies_data=None):
        self.cookies_data = cookies_data

    def setup(self, cookies_data):
        self.cookies_data = cookies_data

    def can_parse_url(self, url):
        return self._regex.match(url) is not None

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None
        cookies = self.get_cookies()
        r = requests.get(url, cookies=cookies, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())
        soup = get_soup(r.text)
        if soup.h1 is None:
            # toloka doesn't return 404 for not existing topic
            # it return regular page with text 'Такої теми чи такого повідомлення не існує'
            # and we can check it by not existing heading of the requested topic
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def login(self, username, password):
        s = Session()
        data = {"username": username, "password": password, 'login': 1}
        if self.tracker_settings:
            login_result = s.post(self.login_url, data, **self.tracker_settings.get_requests_kwargs())
        else:
            login_result = s.post(self.login_url, data)

        if login_result.url.startswith(self.login_url):
            raise TolokaLoginFailedException(1, "Invalid login or password")
        else:
            cookies_data = s.cookies.get('toloka_sid')
            if not cookies_data:
                raise TolokaLoginFailedException(2, "Failed to retrieve cookie")

            self.cookies_data = cookies_data

    def verify(self):
        cookies = self.get_cookies()
        if not cookies:
            return False
        profile_page_result = requests.get(self.profile_page, cookies=cookies,
                                           **self.tracker_settings.get_requests_kwargs())
        return profile_page_result.url == self.profile_page

    def get_cookies(self):
        if not self.cookies_data:
            return False
        return {'toloka_sid': self.cookies_data}

    def get_download_url(self, url):
        cookies = self.get_cookies()
        page = requests.get(url, cookies=cookies, **self.tracker_settings.get_requests_kwargs())
        page_soup = get_soup(page.content)
        download = page_soup.find("a", {"class": "piwik_download"})
        return 'https://toloka.to/%s' % download.attrs['href']

class TolokaPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = TolokaTracker()
    topic_class = TolokaTopic
    credentials_class = TolokaCredentials
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
            if not username or not password:
                return LoginResult.CredentialsNotSpecified
        try:
            self.tracker.login(username, password)
            with DBSession() as db:
                cred = db.query(self.credentials_class).first()
                cred.cookies_data = self.tracker.cookies_data
            return LoginResult.Ok
        except TolokaLoginFailedException as e:
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
            if not username or not password or not cred.cookies_data:
                return False
            self.tracker.setup(cred.cookies_data)
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        headers = {'referer': topic.url, 'host': "toloka.to"}
        cookies = self.tracker.get_cookies()
        request = requests.Request('POST', self.tracker.get_download_url(topic.url), headers=headers, cookies=cookies)
        return request.prepare()

register_plugin('tracker', PLUGIN_NAME, TolokaPlugin())
