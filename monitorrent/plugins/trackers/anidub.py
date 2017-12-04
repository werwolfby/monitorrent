#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import requests
from requests import Session
from sqlalchemy import Column, String, ForeignKey, Integer
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase, \
    LoginResult
from monitorrent.utils.soup import get_soup

PLUGIN_NAME = 'anidub.com'


class AnidubCredentials(Base):
    __tablename__ = "anidub_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    dle_uid = Column(String, nullable=True)
    dle_pwd = Column(String, nullable=True)


class AnidubTopic(Topic):
    __tablename__ = "anidub_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)
    format = Column(String, nullable=False)
    format_list = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class AnidubLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class AnidubTracker(object):
    tracker_settings = None
    _regex = re.compile(r'^http(s?)://tr\.*anidub.com/(?:.*/\d+-.*\.html|(?:index\.php)?\?newsid=\d+)$')
    root_url = "https://tr.anidub.com"

    def __init__(self, dle_uid=None, dle_pwd=None):
        self.dle_uid = dle_uid
        self.dle_pwd = dle_pwd

    def setup(self, dle_uid, dle_pwd):
        self.dle_uid = dle_uid
        self.dle_pwd = dle_pwd

    def can_parse_url(self, url):
        return self._regex.match(url) is not None

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())
        soup = get_soup(r.text)
        title = soup.find('span', id='news-title')
        if title is None:
            return None
        title = title.text.strip()
        result = {'original_name': title}
        # Format
        format_list = []
        flist = self._find_format_list(soup)
        for q in flist:
            format_list.append(q.text.strip())
        result['format_list'] = format_list
        return result

    def login(self, username, password):
        s = Session()
        data = {"login_name": username, "login_password": password, "login": "submit"}
        login_result = s.post(self.root_url, data, **self.tracker_settings.get_requests_kwargs())
        if not self._is_logged_in(login_result.text):
            raise AnidubLoginFailedException(1, "Invalid login or password")
        else:
            dle_uid = s.cookies.get('dle_user_id')
            dle_pwd = s.cookies.get('dle_password')
            if not dle_uid or not dle_pwd:
                raise AnidubLoginFailedException(2, "Failed to retrieve cookies")
            self.dle_uid = dle_uid
            self.dle_pwd = dle_pwd

    def get_cookies(self):
        if not self.dle_uid or not self.dle_pwd:
            return False
        return {'dle_user_id': self.dle_uid, 'dle_password': self.dle_pwd}

    def verify(self):
        cookies = self.get_cookies()
        if not cookies:
            return False
        r = requests.get(self.root_url, cookies=cookies, **self.tracker_settings.get_requests_kwargs())
        return self._is_logged_in(r.text)

    def get_download_url(self, url, vformat):
        cookies = self.get_cookies()
        page = requests.get(url, cookies=cookies, **self.tracker_settings.get_requests_kwargs())
        page_soup = get_soup(page.text)
        flist = self._find_format_list(page_soup)
        for f in flist:
            if f.text.strip() == vformat:
                href = f['href'][1:]
                at = page_soup.select_one('div[class="torrent"] div#'+href+' a')
                return self.root_url + at['href']
        return None

    @staticmethod
    def _find_format_list(soup):
        return soup.select('div#tabs ul[class="lcol"] a')

    def _is_logged_in(self, page):
        return "/index.php?action=logout\"" in page


class AnidubPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = AnidubTracker()
    topic_class = AnidubTopic
    credentials_class = AnidubCredentials
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'status', 'format', 'format_list']
    topic_private_fields = ['display_name', 'format', 'format_list']
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 70
        }, {
            'type': 'select',
            'model': 'format',
            'label': 'Format',
            'options': [],
            'flex': 30
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
                cred.dle_uid = self.tracker.dle_uid
                cred.dle_pwd = self.tracker.dle_pwd
                return LoginResult.Ok
        except AnidubLoginFailedException as e:
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
            if not username or not password or not cred.dle_uid or not cred.dle_pwd:
                return False
            self.tracker.setup(cred.dle_uid, cred.dle_pwd)
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def get_topic(self, id):
        result = super(AnidubPlugin, self).get_topic(id)
        if result is None:
            return None
        # format list
        self.topic_form[0]['content'][1]['options'] = result['format_list'].split(',')
        return result

    def prepare_add_topic(self, url):
        parsed_url = self.tracker.parse_url(url)
        if not parsed_url:
            return None
        # format list
        self.topic_form[0]['content'][1]['options'] = parsed_url['format_list']
        settings = {
            'display_name': parsed_url['original_name'],
            'format': parsed_url['format_list'][0]
        }
        return settings

    def _set_topic_params(self, url, parsed_url, topic, params):
        """
        :param url: str
        :type topic: AnidubTopic
        """
        super(AnidubPlugin, self)._set_topic_params(url, parsed_url, topic, params)
        if parsed_url is not None:
            topic.format_list = ",".join(parsed_url['format_list'])

    def _prepare_request(self, topic):
        url = self.tracker.get_download_url(topic.url, topic.format)
        if url is None:
            return None
        headers = {'referer': topic.url}
        cookies = self.tracker.get_cookies()
        request = requests.Request('GET', url, cookies=cookies, headers=headers)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, AnidubPlugin())
