#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import six
import requests
from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import Base, DBSession, row2dict, dict2row
from monitorrent.plugins import Topic
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.soup import get_soup
from monitorrent.plugins.trackers import TrackerPluginBase, ExecuteWithHashChangeMixin

PLUGIN_NAME = 'hdclub.org'


class HdclubCredentials(Base):
    __tablename__ = "hdclub_credentials"

    passkey = Column(String, nullable=True, primary_key=True)


class HdclubTopic(Topic):
    __tablename__ = "hdclub_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class HdclubTracker(object):
    tracker_settings = None
    url_regex = re.compile(six.text_type(r'^https?://hdclub\.org/details\.php\?id=(\d+)$'))

    def __init__(self, passkey=None):
        self.passkey = passkey

    def setup(self, passkey):
        self.passkey = passkey

    def can_parse_url(self, url):
        return self.url_regex.match(url) is not None

    def parse_url(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False, **self.tracker_settings.get_requests_kwargs())

        soup = get_soup(r.text)
        if soup.h1 is None:
            # Hdclub doesn't return 404 for not existing topic
            # it return regular page with text 'Тема не найдена'
            # and we can check it by not existing heading of the requested topic
            return None
        title = soup.h1.text.strip()

        return {'original_name': title}

    def get_id(self, url):
        match = self.url_regex.match(url)
        if match is None:
            return None

        return int(match.group(1))

    def get_download_url(self, url):
        torrent_id = self.get_id(url)
        if torrent_id is None:
            return None

        if not self.passkey:
            return None

        return "https://hdclub.org/download.php?id={0}&passkey={1}".format(torrent_id, self.passkey)


class HdclubPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = HdclubTracker()
    topic_class = HdclubTopic
    credentials_class = HdclubCredentials
    credentials_public_fields = ['passkey']
    credentials_private_fields = ['passkey']

    credentials_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'passkey',
            'label': 'Passkey',
            'flex': 100
        }]
    }]

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def get_credentials(self):
        with DBSession() as db:
            dbcredentials = db.query(self.credentials_class).first()
            if dbcredentials is None:
                return None
            return row2dict(dbcredentials, None, self.credentials_public_fields)

    def update_credentials(self, credentials):
        with DBSession() as db:
            dbcredentials = db.query(self.credentials_class).first()
            if dbcredentials is None:
                dbcredentials = self.credentials_class()
                db.add(dbcredentials)
            dict2row(dbcredentials, credentials, self.credentials_private_fields)

    def _prepare_request(self, topic):
        return self.tracker.get_download_url(topic.url)

    def execute(self, topics, engine):
        settings = self.get_credentials()
        if not settings:
            return

        passkey = settings['passkey']
        if passkey == "":
            engine.failed("There are no passkey")
            return

        self.tracker.setup(passkey)

        return super(HdclubPlugin, self).execute(topics, engine)


register_plugin('tracker', PLUGIN_NAME, HdclubPlugin())
