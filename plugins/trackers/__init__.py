from db import DBSession, row2dict, dict2row
from plugins import Topic
import abc


class TrackerBase(object):
    @abc.abstractmethod
    def parse_url(self, url):
        """
        :rtype : dict
        """
        pass


class TrackerPluginBase(object):
    """
    :type tracker: TrackerBase
    """
    __metaclass__ = abc.ABCMeta

    tracker_class = TrackerBase
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

    def __init__(self):
        super(TrackerPluginBase, self).__init__()
        self.tracker = self.tracker_class()

    def parse_url(self, url):
        parsed_url = self.tracker.parse_url(url)
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
        """
        parsed_url = self.tracker.parse_url(url)
        if parsed_url is None:
            return False
        with DBSession() as db:
            topic = self.topic_class(url=url)
            self._set_topic_params(topic, parsed_url, params)
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
            self._set_topic_params(topic, None, params)
        return True

    def get_topic_info(self, topic):
        """

        :type topic: object
        :rtype : str
        """
        return None

    def execute(self, ids, engine):
        pass

    def _get_display_name(self, parsed_url):
        """
        :type parsed_url: dict
        """
        return parsed_url['original_name']

    def _set_topic_params(self, topic, parsed_url, params):
        """
        :type topic: Topic
        :type parsed_url: dict | None
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
