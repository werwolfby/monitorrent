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

PLUGIN_NAME = 'kinozal.tv'


class KinozalCredentials(Base):
    __tablename__ = "Kinozal_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    c_uid = Column(String, nullable=True)
    c_pass = Column(String, nullable=True)


class KinozalTopic(Topic):
    __tablename__ = "Kinozal_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class KinozalLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class KinozalTracker(object):
    tracker_settings = None
    login_url = "http://kinozal.tv/takelogin.php"
    profile_page = "http://kinozal.tv/inbox.php"
    url_regex = re.compile(six.text_type(r'^https?://kinozal\.tv/details\.php\?id=(\d+)$'))

    def __init__(self, c_uid=None, c_pass=None):
        self.c_uid = c_uid
        self.c_pass = c_pass

    def setup(self, c_uid, c_pass):
        self.c_uid = c_uid
        self.c_pass = c_pass

    def can_parse_url(self, url):
        return self.url_regex.match(url) is not None

    def parse_url(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())

        soup = get_soup(r.text)
        if soup.h1 is None:
            # Kinozal doesn't return 404 for not existing topic
            # it return regular page with text 'Тема не найдена'
            # and we can check it by not existing heading of the requested topic
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def login(self, username, password):
        s = Session()
        data = {"username": username, "password": password, 'returnto': ''}
        login_result = s.post(self.login_url, data, **self.tracker_settings.get_requests_kwargs())
        if login_result.url.startswith(self.login_url):
            # TODO get error info (although it shouldn't contain anything useful
            # it can contain request to enter capture, so we should handle it
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
        profile_page_result = requests.get(self.profile_page, cookies=cookies,
                                           **self.tracker_settings.get_requests_kwargs())
        return profile_page_result.url == self.profile_page

    def get_cookies(self):
        if not self.c_pass or not self.c_uid:
            return False
        return {'pass': self.c_pass, 'uid': self.c_uid}

    def get_id(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None

        return match.group(1)

    def get_download_url(self, url):
        torrent_id = self.get_id(url)
        if torrent_id is None:
            return None

        return "http://dl.kinozal.tv/download.php?id=" + torrent_id


class KinozalPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = KinozalTracker()
    topic_class = KinozalTopic
    credentials_class = KinozalCredentials
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
                cred.c_uid = self.tracker.c_uid
                cred.c_pass = self.tracker.c_pass
            return LoginResult.Ok
        except KinozalLoginFailedException as e:
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
            if not username or not password or not cred.c_uid or not cred.c_pass:
                return False
            self.tracker.setup(cred.c_uid, cred.c_pass)
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        headers = {'referer': topic.url}
        cookies = self.tracker.get_cookies()
        request = requests.Request('GET', self.tracker.get_download_url(topic.url), headers=headers, cookies=cookies)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, KinozalPlugin())
