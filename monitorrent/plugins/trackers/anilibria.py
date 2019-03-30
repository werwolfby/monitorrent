# -*- coding: utf-8 -*-
import re
import sys
import traceback

import requests
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData, Table

from monitorrent.db import row2dict
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins import Topic, Status
from monitorrent.plugins.trackers import TrackerPluginBase, ExecuteWithHashChangeMixin
from monitorrent.utils.soup import get_soup

PLUGIN_NAME = 'anilibria.tv'


class AnilibriaTvTopic(Topic):
    __tablename__ = "anilibriatv_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)
    format = Column(String, nullable=True)
    format_list = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), AnilibriaTvTopic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        upgrade_0_to_1(operations_factory)
    version = 1


def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(AnilibriaTvTopic.__tablename__, m, autoload=True)
    if 'format' not in topics.columns:
        return 0
    return 1


# noinspection PyProtectedMember
def upgrade_0_to_1(operations_factory):
    from monitorrent.settings_manager import SettingsManager
    settings_manager = SettingsManager()
    tracker_settings = None
    with operations_factory() as operations:
        operations.add_column(AnilibriaTvTopic.__tablename__, Column('format', String, nullable=True))
        operations.add_column(AnilibriaTvTopic.__tablename__, Column('format_list', String, nullable=True))
        topic_values = []
        m = MetaData()
        ani_topics = Table(AnilibriaTvTopic.__tablename__, m,
                           Column("id", Integer, ForeignKey('topics.id'), primary_key=True),
                           Column("hash", String, nullable=True), Column("format", String, nullable=True),
                           Column("format_list", String, nullable=True))
        m1 = MetaData()
        base_topics = Table(Topic.__tablename__, m1, Column("id", Integer, primary_key=True),
                            Column("url", String), Column("type", String), Column('status', String))
        topics = operations.db.query(base_topics).filter(base_topics.c.type == PLUGIN_NAME)
        for topic in topics:
            raw_topic = row2dict(topic, base_topics)
            # noinspection PyBroadException
            try:
                if tracker_settings is None:
                    tracker_settings = settings_manager.tracker_settings
                response = requests.get(raw_topic['url'], **tracker_settings.get_requests_kwargs())
                soup = get_soup(response.text)
                format_list = AnilibriaTvTracker._find_format_list(soup)
                format_list.sort()
                topic_values.append({'id': raw_topic['id'], 'format_list': ",".join(format_list),
                                     'format': format_list[0],
                                     'status': Status.Ok.__str__()})
            except:
                exc_info = sys.exc_info()
                print(u''.join(traceback.format_exception(*exc_info)))
                topic_values.append({'id': raw_topic['id'], 'status': Status.Error.__str__()})

        for upd in topic_values:
            if 'format' in upd:
                operations.db.execute(ani_topics.update(whereclause=(ani_topics.c.id == upd['id']),
                                                        values={'format_list': upd['format_list'],
                                                                'format': upd['format']}))
            operations.db.execute(base_topics.update(whereclause=(base_topics.c.id == upd['id']),
                                                     values={'status': upd['status']}))


class AnilibriaTvTracker(object):
    tracker_settings = None
    _tracker_regex = re.compile(r'^https://(www\.)?anilibria.tv/release/.*\.html$')
    _title_regex = re.compile(r'^.* / .*$')
    _format_regex = re.compile(r'^.*\[(.*)\]$')

    def can_parse_url(self, url):
        return self._tracker_regex.match(url) is not None

    def parse_url(self, url):
        if not self.can_parse_url(url):
            return None

        match = self._tracker_regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=True, **self.tracker_settings.get_requests_kwargs())
        soup = get_soup(r.text)

        title = soup.title.string

        if self._title_regex.match(title) is None:
            return None

        format_list = self._find_format_list(soup)
        if format_list is not None:
            format_list.sort()

        return {'original_name': title, 'format_list': format_list}

    def get_download_url(self, url, vformat):
        if not self.can_parse_url(url):
            return None

        match = self._tracker_regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=True, **self.tracker_settings.get_requests_kwargs())
        soup = get_soup(r.text)

        flist = self._find_format_list(soup)

        try:
            torrent_idx = -1

            if flist is not None and vformat is not None:
                torrent_idx = flist.index(vformat) if vformat in flist else -1

            a = soup.find_all("a", class_="torrent-download-link")[torrent_idx]
        except IndexError:
            return None

        return None if a is None else "https://www.anilibria.tv" + a["href"]

    @staticmethod
    def _find_format_list(soup):
        raw_list = soup.select('table#publicTorrentTable td[class="torrentcol1"]')
        format_list = []
        for f in raw_list:
            match = AnilibriaTvTracker._format_regex.match(f.text)
            if match:
                format_list.append(match.group(1))
        return format_list


class AnilibriaTvPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = AnilibriaTvTracker()
    topic_class = AnilibriaTvTopic
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'status', 'format', 'format_list']
    topic_private_fields = ['display_name', 'format', 'format_list']
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 60
        }, {
            'type': 'select',
            'model': 'format',
            'label': 'Format',
            'options': [],
            'flex': 40
        }]
    }]

    def can_parse_url(self, url):
        return self.tracker.can_parse_url(url)

    def parse_url(self, url):
        return self.tracker.parse_url(url)

    # noinspection PyShadowingBuiltins
    def get_topic(self, id):
        result = super(AnilibriaTvPlugin, self).get_topic(id)
        if result is None:
            return None
        if result['format_list'] is not None:
            format_list = result['format_list'].split(',')
        else:
            format_list = []
        self._set_format_list(format_list)
        return result

    def prepare_add_topic(self, url):
        parsed_url = self.tracker.parse_url(url)
        if not parsed_url:
            return None
        self._set_format_list(parsed_url['format_list'])
        settings = {
            'display_name': parsed_url['original_name'],
            'format': parsed_url['format_list'][0]
        }
        return settings

    def _set_format_list(self, format_list):
        self.topic_form[0]['content'][1]['options'] = format_list

    def _prepare_request(self, topic):
        url = self.tracker.get_download_url(topic.url, topic.format)
        if url is None:
            return None
        headers = {'referer': topic.url}
        request = requests.Request('GET', url, headers=headers)
        return request.prepare()

    def _set_topic_params(self, url, parsed_url, topic, params):
        super(AnilibriaTvPlugin, self)._set_topic_params(self, parsed_url, topic, params)
        if parsed_url is not None and parsed_url['format_list'] is not None:
            topic.format_list = ",".join(parsed_url['format_list'])


register_plugin('tracker', PLUGIN_NAME, AnilibriaTvPlugin(), upgrade=upgrade)
