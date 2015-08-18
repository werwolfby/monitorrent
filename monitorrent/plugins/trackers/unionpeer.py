#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from urlparse import urlparse
from bs4 import BeautifulSoup
import requests
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, ForeignKey
from monitorrent.db import row2dict
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase
from monitorrent.utils.bittorrent import Torrent

PLUGIN_NAME = 'unionpeer.org'


class UnionpeerOrgTopic(Topic):
    __tablename__ = "unionpeerorg_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), UnionpeerOrgTopic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        upgrade_0_to_1(engine, operations_factory)
        version = 1


def get_current_version(engine):
    m = MetaData(engine)
    t = Table(UnionpeerOrgTopic.__tablename__, m, autoload=True)
    if 'hash' in t.columns and not t.columns['hash'].nullable:
        return 0
    return 1


def upgrade_0_to_1(engine, operations_factory):
    m1 = MetaData()
    unionpeer_topic_table_0 = Table('unionpeerorg_topics', m1,
                                    Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                                    Column("hash", String, nullable=False))

    m2 = MetaData()
    unionpeer_topic_table_1 = Table('unionpeerorg_topics1', m2,
                                    Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                                    Column("hash", String, nullable=True))
    with operations_factory() as operations:
        operations.create_table(unionpeer_topic_table_1)
        topics = operations.db.query(unionpeer_topic_table_0)
        for topic in topics:
            raw_topic = row2dict(topic, unionpeer_topic_table_0)
            operations.db.execute(unionpeer_topic_table_1.insert(), raw_topic)
        operations.drop_table(unionpeer_topic_table_0)
        operations.rename_table(unionpeer_topic_table_1.name, unionpeer_topic_table_0.name)


class UnionpeerOrgTracker(object):
    _regex = re.compile(ur'^/topic/(\d+)(-.*)?$')
    title_header = u"скачать торрент "

    def can_parse_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc.endswith('.unionpeer.org') or parsed_url.netloc == 'unionpeer.org'

    def parse_url(self, url):
        if not self.can_parse_url(url):
            return None

        parsed_url = urlparse(url)
        match = self._regex.match(parsed_url.path)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=False)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.content)
        title = soup.h1.string.strip()
        if title.lower().startswith(self.title_header):
            title = title[len(self.title_header):].strip()

        return self._get_title(title)

    def get_hash(self, url):
        download_url = self.get_download_url(url)
        if not download_url:
            return None
        r = requests.get(download_url)
        t = Torrent(r.content)
        return t.info_hash

    def get_id(self, url):
        match = self._regex.match(url)
        if match is None:
            return None

        return match.group(1)

    def get_download_url(self, url):
        if not self.can_parse_url(url):
            return None
        parsed_url = urlparse(url)

        return "http://unionpeer.org/dl.php?t=" + self.get_id(parsed_url.path)

    @staticmethod
    def _get_title(title):
        return {'original_name': title}


class UnionpeerOrgPlugin(TrackerPluginBase):
    tracker = UnionpeerOrgTracker()
    topic_class = UnionpeerOrgTopic
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    def _prepare_request(self, topic):
        return self.tracker.get_download_url(topic.url)


register_plugin('tracker', PLUGIN_NAME, UnionpeerOrgPlugin(), upgrade=upgrade)
