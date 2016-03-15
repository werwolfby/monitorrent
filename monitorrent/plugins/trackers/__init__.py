import abc
import cgi
from enum import Enum
from monitorrent.db import DBSession, row2dict, dict2row
from monitorrent.plugins import Topic, Status
from monitorrent.utils.bittorrent import Torrent
from monitorrent.utils.downloader import download
from monitorrent.engine import Engine


class TrackerSettings:
    def __init__(self, requests_timeout):
        self.requests_timeout = requests_timeout


class TrackerPluginBase(object):
    __metaclass__ = abc.ABCMeta

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
    :type plugin_settings: PluginSettings
    """
    def init(self, tracker_settings):
        self.tracker_settings = tracker_settings
        if hasattr(self, 'tracker') and hasattr(self.tracker, 'tracker_settings'):
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
            topics = db.query(self.topic_class)\
                .filter(self.topic_class.status.in_((Status.Ok, Status.Error)))\
                .all()
            db.expunge_all()
        return topics

    def save_topic(self, topic, last_update, status=Status.Ok):
        if not isinstance(topic, self.topic_class):
            raise Exception("Can't update topic of wrong class. Expected {0}, but was {1}"
                            .format(self.topic_class, topic.__class__))

        with DBSession() as db:
            db_serie = topic
            if last_update is not None:
                db_serie.last_update = last_update
            db_serie.status = status
            db.add(topic)
            db.commit()

    def get_topic(self, id):
        with DBSession() as db:
            topic = db.query(self.topic_class).filter(Topic.id == id).first()
            if topic is None:
                return None
            data = row2dict(topic, None, self.topic_public_fields)
            data['info'] = self.get_topic_info(topic)
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
    def execute(self, ids, engine):
        """
        :type ids: list[int] | None
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
        :type parsed_url: dict | None
        :type topic: Topic
        :type params: dict
        """
        dict2row(topic, params, self.topic_private_fields)


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

    def execute(self, ids, engine):
        """
        :type ids: list[int] | None
        :type engine: Engine
        :return: None
        """
        topics = self.get_topics(ids)
        for topic in topics:
            topic_name = topic.display_name
            try:
                engine.log.info(u"Check for changes <b>%s</b>" % topic_name)
                prepared_request = self._prepare_request(topic)
                download_kwargs = {}
                if isinstance(prepared_request, tuple) and len(prepared_request) >= 2:
                    download_kwargs = prepared_request[1] or download_kwargs
                    prepared_request = prepared_request[0]
                download_kwargs.setdefault('timeout', self.tracker_settings.requests_timeout)
                response, filename = download(prepared_request, **download_kwargs)
                if hasattr(self, 'check_download'):
                    status = self.check_download(response)
                    if topic.status != status:
                        with DBSession() as db:
                            db.add(topic)
                            topic.status = status
                            db.commit()
                    if status != Status.Ok:
                        engine.log.failed(u"Torrent status changed: {}".format(status))
                        continue
                elif response.status_code != 200:
                    raise Exception("Can't download url. Status: {}".format(response.status_code))
                if not filename:
                    filename = topic_name
                engine.log.info(u"Downloading <b>%s</b> torrent" % filename)
                torrent_content = response.content
                torrent = Torrent(torrent_content)
                old_hash = topic.hash
                if torrent.info_hash != old_hash:
                    engine.log.downloaded(u"Torrent <b>%s</b> was changed" % topic_name, torrent_content)
                    last_update = engine.add_torrent(filename, torrent, old_hash)
                    with DBSession() as db:
                        db.add(topic)
                        topic.hash = torrent.info_hash
                        topic.last_update = last_update
                        db.commit()
                else:
                    engine.log.info(u"Torrent <b>%s</b> not changed" % topic_name)
            except Exception as e:
                engine.log.failed(u"Failed update <b>%s</b>.\nReason: %s" % (topic_name, cgi.escape(unicode(e))))


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
class WithCredentialsMixin(TrackerPluginMixinBase):
    __metaclass__ = abc.ABCMeta

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

    def execute(self, ids, engine):
        if not self._execute_login(engine):
            return
        super(WithCredentialsMixin, self).execute(ids, engine)

    def _execute_login(self, engine):
        if not self.verify():
            engine.log.info(u"Credentials/Settings are not valid\nTry login.")
            login_result = self.login()
            if login_result == LoginResult.CredentialsNotSpecified:
                engine.log.info(u"Credentials not specified\nSkip plugin")
                return False
            if login_result != LoginResult.Ok:
                engine.log.failed(u"Can't login: {}".format(login_result))
                return False
            engine.log.info(u"Login successful")
            return True
        engine.log.info(u"Credentials/Settings are valid")
        return True
