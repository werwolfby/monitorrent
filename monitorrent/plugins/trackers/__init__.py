import abc
import html

import cloudscraper
import requests
import six
import pprint
from enum import Enum

import urllib3.util
from cloudscraper.exceptions import CloudflareException
from playwright.sync_api import sync_playwright
from urllib3.util import Url

from monitorrent.db import DBSession, row2dict, dict2row
from monitorrent.plugins import Topic
from monitorrent.plugins.status import Status
from monitorrent.plugins.clients import TopicSettings
from monitorrent.utils.bittorrent_ex import Torrent, is_torrent_content
from monitorrent.utils.downloader import download
from monitorrent.engine import Engine
from future.utils import with_metaclass


class TrackerSettings(object):
    def __init__(self, requests_timeout, proxies):
        self.requests_timeout = requests_timeout
        self.proxies = proxies

    def get_requests_kwargs(self):
        return {'timeout': self.requests_timeout, 'proxies': self.proxies}


class TrackerPluginBase(with_metaclass(abc.ABCMeta, object)):
    tracker_settings = None
    topic_class = Topic
    topic_public_fields = ['id', 'url', 'last_update', 'display_name', 'status']
    topic_private_fields = ['display_name']
    topic_form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'model': 'display_name',
            'label': 'Name',
            'flex': 100
        }]
    }]

    """
    :type tracker_settings: TrackerSettings
    """
    def init(self, tracker_settings):
        self.tracker_settings = tracker_settings
        # pylint: disable=E1101
        if hasattr(self, 'tracker') and hasattr(self.tracker, 'tracker_settings'):
            # pylint: disable=E1101
            self.tracker.tracker_settings = tracker_settings

    @abc.abstractmethod
    def can_parse_url(self, url):
        """
        Check if we can parse url

        :param url: str
        :rtype: bool
        """

    @abc.abstractmethod
    def parse_url(self, url):
        """
        Parse url and extract all information from url to topic

        :param url: str
        :rtype: dict
        """

    def prepare_add_topic(self, url):
        parsed_url = self.parse_url(url)
        if not parsed_url:
            return None
        settings = {
            'display_name': self._get_display_name(parsed_url),
        }
        return settings

    def add_topic(self, url, params):
        """
        :type url: str
        :type params: dict
        :rtype: bool
        """
        parsed_url = self.parse_url(url)
        if parsed_url is None:
            # TODO: Throw exception, because we shouldn't call add topic if we can't parse URL
            return False
        with DBSession() as db:
            topic = self.topic_class(url=url)
            self._set_topic_params(url, parsed_url, topic, params)
            db.add(topic)
        return True

    def get_topics(self, ids):
        with DBSession() as db:
            if ids is not None and len(ids) > 0:
                filter_query = self.topic_class.id.in_(ids)
            else:
                filter_query = self.topic_class.status.in_((Status.Ok, Status.Error))
            filter_query &= self.topic_class.paused == False
            topics = db.query(self.topic_class)\
                .filter(filter_query)\
                .all()
            db.expunge_all()
        return topics

    def save_topic(self, topic, last_update, status=Status.Ok):
        if not isinstance(topic, self.topic_class):
            raise Exception(u"Can't update topic of wrong class. Expected {0}, but was {1}"
                            .format(self.topic_class, topic.__class__))

        with DBSession() as db:
            new_topic = topic
            if last_update is not None:
                new_topic.last_update = last_update
            new_topic.status = status
            db.add(new_topic)
            db.flush()
            db.expunge(new_topic)

    def save_status(self, topic_id, status):
        with DBSession() as db:
            topic = db.query(self.topic_class).filter(Topic.id == topic_id).first()
            topic.status = status

    def get_topic(self, id):
        with DBSession() as db:
            topic = db.query(self.topic_class).filter(Topic.id == id).first()
            if topic is None:
                return None
            data = row2dict(topic, None, self.topic_public_fields)
            data['info'] = self.get_topic_info(topic)
            data['download_dir'] = topic.download_dir
            return data

    def update_topic(self, id, params):
        with DBSession() as db:
            topic = db.query(self.topic_class).filter(Topic.id == id).first()
            if topic is None:
                return False
            self._set_topic_params(None, None, topic, params)
        return True

    def get_topic_info(self, topic):
        """

        :type topic: object
        :rtype : str
        """
        return None

    @abc.abstractmethod
    def execute(self, topics, engine):
        """
        :param topics: result of get_topics func
        :type engine: Engine
        :return: None
        """

    @abc.abstractmethod
    def _prepare_request(self, topic):
        """
        """

    def _get_display_name(self, parsed_url):
        """
        :type parsed_url: dict
        """
        return parsed_url['original_name']

    def _set_topic_params(self, url, parsed_url, topic, params):
        """

        :type url: str | None
        :type parsed_url: object | dict | None
        :type topic: Topic
        :type params: dict
        """
        fields = None
        if self.topic_private_fields is not None:
            fields = self.topic_private_fields + ['download_dir']
        dict2row(topic, params, fields)


class TrackerPluginMixinBase(object):
    def __init__(self):
        if not isinstance(self, TrackerPluginBase):
            raise Exception('TrackerPluginMixinBase can be applied only to TrackerPluginBase classes')
        super(TrackerPluginMixinBase, self).__init__()


# noinspection PyUnresolvedReferences
class ExecuteWithHashChangeMixin(TrackerPluginMixinBase):
    def __init__(self):
        super(ExecuteWithHashChangeMixin, self).__init__()
        if not hasattr(self.topic_class, 'hash'):
            raise Exception("ExecuteWithHashMixin can be applied only to TrackerPluginBase class "
                            "with hash attribute in topic_class")

    def execute(self, topics, engine):
        """
        :param topics: result of get_topics func
        :type engine: engine.EngineTracker
        :return: None
        """
        with engine.start(len(topics)) as engine_topics:
            for i in range(0, len(topics)):
                topic = topics[i]
                topic_name = topic.display_name
                with engine_topics.start(i, topic_name) as engine_topic:
                    changed = False
                    if hasattr(self, 'check_changes'):
                        changed = self.check_changes(topic)
                        if not changed:
                            continue

                    prepared_request = self._prepare_request(topic)
                    download_kwargs = dict(self.tracker_settings.get_requests_kwargs())
                    if isinstance(prepared_request, tuple) and len(prepared_request) >= 2:
                        if prepared_request[1] is not None:
                            download_kwargs.update(prepared_request[1])
                        prepared_request = prepared_request[0]
                    response, filename = download(prepared_request, **download_kwargs)
                    if hasattr(self, 'check_download'):
                        status = self.check_download(response)
                        if topic.status != status:
                            self.save_status(topic.id, status)
                            engine_topic.status_changed(topic.status, status)
                        if status != Status.Ok:
                            continue
                    elif response.status_code != 200:
                        raise Exception(u"Can't download url. Status: {}".format(response.status_code))
                    if not filename:
                        filename = topic_name
                    torrent_content = response.content
                    if not is_torrent_content(torrent_content):
                        headers = ['{0}: {1}'.format(k, v) for k, v in six.iteritems(response.headers)]
                        engine.failed(u'Downloaded content is not a torrent file.<br>\r\n'
                                      u'Headers:<br>\r\n{0}'.format(u'<br>\r\n'.join(headers)))
                        continue
                    torrent = Torrent(torrent_content)
                    old_hash = topic.hash
                    if torrent.info_hash != old_hash:
                        with engine_topic.start(1) as engine_downloads:
                            last_update = engine_downloads.add_torrent(0, filename, torrent, old_hash,
                                                                       TopicSettings.from_topic(topic))
                            engine.downloaded(u"Torrent <b>{0}</b> was changed".format(topic_name), torrent_content)
                            topic.hash = torrent.info_hash
                            topic.last_update = last_update
                            self.save_topic(topic, last_update, Status.Ok)
                    elif changed:
                        engine.info(u"Torrent <b>{0}</b> was determined as changed, but torrent hash wasn't"
                                    .format(topic_name))
                        self.save_topic(topic, None, Status.Ok)


class LoginResult(Enum):
    Ok = 1
    CredentialsNotSpecified = 2
    IncorrentLoginPassword = 3
    InternalServerError = 500
    ServiceUnavailable = 503
    Unknown = 999

    def __str__(self):
        if self == LoginResult.Ok:
            return u"Ok"
        if self == LoginResult.CredentialsNotSpecified:
            return u"Credentials not specified"
        if self == LoginResult.IncorrentLoginPassword:
            return u"Incorrent login/password"
        if self == LoginResult.InternalServerError:
            return u"Internal server error"
        if self == LoginResult.ServiceUnavailable:
            return u"Service unavailable"
        return u"Unknown"


# noinspection PyUnresolvedReferences
class WithCredentialsMixin(with_metaclass(abc.ABCMeta, TrackerPluginMixinBase)):
    credentials_class = None
    credentials_public_fields = ['username']
    credentials_private_fields = ['username', 'password']

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
    }]

    @abc.abstractmethod
    def login(self):
        """
        :rtype: LoginResult
        """

    @abc.abstractmethod
    def verify(self):
        """
        :rtype: bool
        """

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
        return self.login()

    def execute(self, ids, engine):
        if not self._execute_login(engine):
            return
        super(WithCredentialsMixin, self).execute(ids, engine)

    def _execute_login(self, engine):
        if not self.verify():
            engine.info(u"Credentials/Settings are not valid\nTry login.")
            login_result = self.login()
            if login_result == LoginResult.CredentialsNotSpecified:
                engine.info(u"Credentials not specified\nSkip plugin")
                return False
            if login_result != LoginResult.Ok:
                engine.failed(u"Can't login: {}".format(login_result))
                return False
            engine.info(u"Login successful")
            return True
        engine.info(u"Credentials/Settings are valid")
        return True


class CloudflareCookiesExtractor(object):
    def __init__(self, url: str):
        self.url = url
        self.url_parse: Url = urllib3.util.parse_url(url)

    def extract_credentials(self, headers, cookies):
        scrapper = cloudscraper.create_scraper()

        try:
            resp = scrapper.get(url=self.url, headers=headers, cookies=cookies)
            if 'Cloudflare' in resp.text:
                raise CloudflareException('Exception should be thrown by scrapper, but this is not always happened')

            # If page doesn't have cloudflare, don't send new cookies and headers
            return headers, cookies
        except CloudflareException as e:
            with sync_playwright() as p:
                browser = p.firefox.launch()
                context = browser.new_context()
                page = context.new_page()

                req_headers = {}

                def on_request(req):
                    all_headers = req.all_headers()
                    nonlocal req_headers
                    req_headers['User-Agent'] = all_headers['user-agent']

                page.on('request', on_request)
                page.goto(self.url)
                page.wait_for_selector('.left-side > .menu', timeout=30000)

                new_cookies = {}
                while 'cf_clearance' not in new_cookies:
                    page_cookies = context.cookies(self.url_parse.scheme + "://" + self.url_parse.hostname)
                    new_cookies = {k['name']: k['value'] for k in page_cookies if k['name'] in ['cf_clearance']}

                return req_headers, new_cookies
