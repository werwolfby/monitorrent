from db import DBSession, row2dict, dict2row
from plugins import Topic
import abc


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
    def parse_url(self, url):
        """
        :rtype : dict
        """
        pass

    def add_topic(self, params):
        """
        :type params: dict
        """
        parsed_url = self.parse_url(params['url'])
        if parsed_url is None:
            return False
        with DBSession() as db:
            topic = self.topic_class()
            # we can set url only when add new topic, that is why in doesn't exist in private fields
            dict2row(topic, params, self.topic_private_fields + ['url'])
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
            dict2row(topic, params, self.topic_private_fields)
        return True

    def remove_topic(self, id):
        with DBSession() as db:
            topic = db.query(self.topic_class).filter(Topic.id == id).first()
            if topic is None:
                return False
            db.remove(topic)
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
        return parsed_url['original_name']


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
