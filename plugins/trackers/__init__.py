import abc
import datetime
from db import DBSession, row2dict, dict2row
from plugins import Topic
from utils.bittorrent import Torrent
from utils.downloader import download
from engine import Engine


class TrackerPluginBase(object):
    __metaclass__ = abc.ABCMeta

    topic_class = Topic
    topic_public_fields = ['id', 'url', 'last_update', 'display_name']
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

    @abc.abstractmethod
    def can_parse_url(self, url):
        """
        Check if we can parse url

        :param url: str
        :rtype: bool
        """
        return False

    @abc.abstractmethod
    def parse_url(self, url):
        """
        Parse url and extract all information from url to topic

        :param url: str
        :rtype: dict
        """
        pass

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

    def execute(self, ids, engine):
        """

        :type ids: list[int] | None
        :type engine: Engine
        :return: None
        """
        with DBSession() as db:
            topics = db.query(self.topic_class).all()
            db.expunge_all()
        for topic in topics:
            topic_name = topic.display_name
            try:
                engine.log.info(u"Check for changes <b>%s</b>" % topic_name)
                torrent_content, filename = download(self._prepare_request(topic))
                engine.log.downloaded(u"Torrent <b>%s</b> downloaded" % filename or topic_name, torrent_content)
                torrent = Torrent(torrent_content)
                if torrent.info_hash != topic.hash:
                    engine.log.info(u"Torrent <b>%s</b> was changed" % topic_name)
                    existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        engine.log.info(u"Torrent <b>%s</b> already added" % filename or topic_name)
                    elif engine.add_torrent(torrent_content):
                        old_existing_torrent = engine.find_torrent(topic.hash)
                        if old_existing_torrent:
                            engine.log.info(u"Updated <b>%s</b>" % filename or topic_name)
                        else:
                            engine.log.info(u"Add new <b>%s</b>" % filename or topic_name)
                        if old_existing_torrent:
                            if engine.remove_torrent(topic.hash):
                                engine.log.info(u"Remove old torrent <b>%s</b>" %
                                                old_existing_torrent['name'])
                            else:
                                engine.log.failed(u"Can't remove old torrent <b>%s</b>" %
                                                  old_existing_torrent['name'])
                        existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        last_update = existing_torrent['date_added']
                    else:
                        last_update = datetime.datetime.now()
                    with DBSession() as db:
                        db.add(topic)
                        topic.hash = torrent.info_hash
                        topic.last_update = last_update
                        db.commit()
                else:
                    engine.log.info(u"Torrent <b>%s</b> not changed" % topic_name)
            except Exception as e:
                engine.log.failed(u"Failed update <b>%s</b>.\nReason: %s" % (topic_name, e.message))

    @abc.abstractmethod
    def _prepare_request(self, topic):
        pass

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


class TrackerPluginWithCredentialsBase(TrackerPluginBase):
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
        pass

    @abc.abstractmethod
    def verify(self):
        pass

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

    def _get_credentials(self, credentials, public):
        """
        :type credentials: dict
        :type public: bool
        """
        fields = self.credentials_public_fields if public else self.credentials_private_fields
        return {(k, v) for k, v in credentials.iteritems() if k in fields}
