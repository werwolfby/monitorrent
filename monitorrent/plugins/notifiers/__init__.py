# coding=utf-8
import inspect
from abc import ABCMeta, abstractproperty, abstractmethod
from sqlalchemy import String, Column, Integer, Boolean
from monitorrent.db import DBSession, dict2row, row2dict, Base


class NotifierPolymorphicMap(dict):
    def __getitem__(self, key):
        return super(NotifierPolymorphicMap, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(NotifierPolymorphicMap, self).__setitem__(key, value)


class Notifier(Base):
    __tablename__ = 'notifiers'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    is_enabled = Column(Boolean)

    def __props__(self):
        pr = {}
        for name in dir(self):
            value = getattr(self, name)
            if not name.startswith('_') and not inspect.ismethod(value) and not name == 'metadata':
                pr[name] = value
        return pr

    __mapper_args__ = {
        'polymorphic_identity': 'topic',
        'polymorphic_on': type,
        'with_polymorphic': '*',
        '_polymorphic_map': NotifierPolymorphicMap()
    }


class NotificationException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class NotifierPlugin:
    def __init__(self):
        """
        pass
        """

    settings_fields = ['access_token', 'user_id']

    __metaclass__ = ABCMeta

    @abstractproperty
    def settings_class(self):
        """
        Returns the settings class for given notifier plugin
        """

    @abstractmethod
    def notify(self, header, body, url=None):
        """

        Notifies the target on incoming message

        :param header: The message header/title/topic
        :param body: The body of the message. Main content.
        :param url: The link to include with the message
        """

    def update_settings(self, settings):
        settings = settings if isinstance(settings, dict) else settings.__dict__
        with DBSession() as db:
            dbsettings = db.query(self.settings_class).first()
            if dbsettings is None:
                dbsettings = self.settings_class()
                db.add(dbsettings)
            else:
                settings['id'] = dbsettings.id
            dict2row(dbsettings, settings)
            return True

    def get_settings(self):
        with DBSession() as db:
            db_settings = db.query(self.settings_class).first()
            if db_settings is None:
                return None
            db.expunge_all()
            return db_settings

