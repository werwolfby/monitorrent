# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()
from builtins import object
import re
from requests import Session
import requests
import urllib.request, urllib.parse, urllib.error
from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import Base, DBSession
from monitorrent.plugins import Topic
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.utils.bittorrent import Torrent
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, ExecuteWithHashChangeMixin, LoginResult

PLUGIN_NAME = 'free-torrents.org'


class FreeTorrentsOrgCredentials(Base):
    __tablename__ = "freetorrents_credentials"

    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    uid = Column(String, nullable=True)
    bbe_data = Column(String, nullable=True)


class FreeTorrentsOrgTopic(Topic):
    __tablename__ = "freetorrents_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class FreeTorrentsLoginFailedException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class FreeTorrentsOrgTracker(object):
    tracker_settings = None
    login_url = "http://login.free-torrents.org/forum/login.php"
    profile_page = "http://free-torrents.org/forum/profile.php?mode=viewprofile&u={}"
    _regex = re.compile(u'^http://w*\.*free-torrents?.org/forum/viewtopic\d?.php\?t=(\d+)(/.*)?$')
    uid_regex = re.compile(u'.*;i:(\d*).*')

    def __init__(self, uid=None, bbe_data=None):
        self.uid = uid
        self.bbe_data = bbe_data

    def setup(self, uid, bbe_data):
        self.uid = uid
        self.bbe_data = bbe_data

    def can_parse_url(self, url):
        return self._regex.match(url) is not None

    def parse_url(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=True, timeout=self.tracker_settings.requests_timeout)

        soup = get_soup(r.content)
        if soup.h1 is None:
            # rutracker doesn't return 404 for not existing topic
            # it return regular page with text 'Тема не найдена'
            # and we can check it by not existing heading of the requested topic
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def login(self, username, password):
        s = Session()
        data = {"login_username": username, "login_password": password, 'login': u'%E2%F5%EE%E4'}
        login_result = s.post(self.login_url, data, headers={'Content-Type': 'application/x-www-form-urlencoded'},
                              timeout=self.tracker_settings.requests_timeout)
        if login_result.url.startswith(self.login_url):
            # TODO get error info (although it shouldn't contain anything useful
            raise FreeTorrentsLoginFailedException(1, "Invalid login or password")
        else:
            bbe_data = s.cookies.get('bbe_data')
            if not bbe_data:
                raise FreeTorrentsLoginFailedException(2, "Failed to retrieve cookie")

            self.bbe_data = bbe_data
            bbe_data_decoded = urllib.parse.unquote(bbe_data)
            self.uid = self.uid_regex.match(bbe_data_decoded).group(1)

    def verify(self):
        if not self.uid:
            return False
        cookies = self.get_cookies()
        if not cookies:
            return False
        profile_page_url = self.profile_page.format(self.uid)
        profile_page_result = requests.get(profile_page_url, cookies=cookies,
                                           timeout=self.tracker_settings.requests_timeout)
        return profile_page_result.url == profile_page_url

    def get_cookies(self):
        if not self.bbe_data:
            return False
        return {'bbe_data': self.bbe_data}

    def get_download_url(self, url):
        cookies = self.get_cookies()
        page = requests.get(url, cookies=cookies, timeout=self.tracker_settings.requests_timeout)
        page_soup = get_soup(page.content)
        download = page_soup.find("a", {"class": "genmed"})
        return download.attrs['href']


class FreeTorrentsOrgPlugin(WithCredentialsMixin, ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = FreeTorrentsOrgTracker()
    topic_class = FreeTorrentsOrgTopic
    credentials_class = FreeTorrentsOrgCredentials
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
                cred.uid = self.tracker.uid
                cred.bbe_data = self.tracker.bbe_data
            return LoginResult.Ok
        except FreeTorrentsLoginFailedException as e:
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
            if not username or not password or not cred.uid or not cred.bbe_data:
                return False
            self.tracker.setup(cred.uid, cred.bbe_data)
        return self.tracker.verify()

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        headers = {'referer': topic.url, 'host': "dl.free-torrents.org"}
        cookies = self.tracker.get_cookies()
        request = requests.Request('GET', self.tracker.get_download_url(topic.url), headers=headers, cookies=cookies)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, FreeTorrentsOrgPlugin())
