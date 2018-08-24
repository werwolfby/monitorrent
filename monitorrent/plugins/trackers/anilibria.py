# -*- coding: utf-8 -*-
import re
import requests
from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, ExecuteWithHashChangeMixin
from monitorrent.utils.soup import get_soup

PLUGIN_NAME = 'anilibria.tv'


class AnilibriaTvTopic(Topic):
    __tablename__ = "anilibriatv_topics"

    id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    hash = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class AnilibriaTvTracker(object):
    tracker_settings = None
    tracker_domain = 'anilibria.tv'
    # _regex = re.compile(u'^/release/.*$')
    _tracker_regex = re.compile(r'^https://(www\.)?anilibria.tv/release/.*\.html$')
    title_end = u' - смотреть онлайн, скачать бесплатно'

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

        if not soup.title.string.endswith(self.title_end):
            return None

        title = soup.title.string[:-len(self.title_end)].strip()

        return {'original_name': title}

    def get_download_url(self, url):
        if not self.can_parse_url(url):
            return None

        match = self._tracker_regex.match(url)
        if match is None:
            return None

        r = requests.get(url, allow_redirects=True, **self.tracker_settings.get_requests_kwargs())
        soup = get_soup(r.text)

        try:
            a = soup.find_all("a", class_="torrent-download-link")[-1]
        except IndexError:
            return None

        return None if a is None else "https://www."+self.tracker_domain+a["href"];


class AnilibriaTvPlugin(ExecuteWithHashChangeMixin, TrackerPluginBase):
    tracker = AnilibriaTvTracker()
    topic_class = AnilibriaTvTopic
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
        url = self.tracker.get_download_url(topic.url)
        if url is None:
            return None
        headers = {'referer': topic.url}
        request = requests.Request('GET', url, headers=headers)
        return request.prepare()


register_plugin('tracker', PLUGIN_NAME, AnilibriaTvPlugin())
