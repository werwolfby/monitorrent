# coding=utf-8
import six
import inspect
from abc import ABCMeta, abstractproperty, abstractmethod

from enum import Enum
from sqlalchemy import String, Column, Integer, Boolean
from monitorrent.db import DBSession, dict2row, row2dict, Base


class NotifierPolymorphicMap(dict):
    def __getitem__(self, key):
        return super(NotifierPolymorphicMap, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(NotifierPolymorphicMap, self).__setitem__(key, value)


class NotifierType(Enum):
    full_text = 1
    short_text = 2


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
    __metaclass__ = ABCMeta
    settings_fields = []

    def __init__(self):
        pass

    @abstractproperty
    def get_type(self):
        """
        Returns the type of the plugin
        """

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

    @property
    def is_enabled(self):
        with DBSession() as db:
            dbsettings = db.query(self.settings_class).first()
            return dbsettings.is_enabled if dbsettings else False

    @is_enabled.setter
    def is_enabled(self, value):
        with DBSession() as db:
            dbsettings = db.query(self.settings_class).first()
            if dbsettings is None:
                raise Exception("Can't enable notifier without settings")
            dbsettings.is_enabled = value

    def update_settings(self, settings):
        settings = settings if isinstance(settings, dict) else settings.__dict__
        settings = {k: v for (k, v) in six.iteritems(settings) if k in self.settings_fields}
        remove = all([v is None or v == "" or v == 0 or v == False for v in six.itervalues(settings)])
        with DBSession() as db:
            dbsettings = db.query(self.settings_class).first()
            if dbsettings is None and not remove:
                dbsettings = self.settings_class()
                db.add(dbsettings)

            if dbsettings is not None:
                if remove:
                    db.delete(dbsettings)
                else:
                    settings['is_enabled'] = dbsettings.is_enabled if dbsettings.is_enabled is not None else True
                    dict2row(dbsettings, settings)
            return True

    def get_settings(self):
        with DBSession() as db:
            db_settings = db.query(self.settings_class).first()
            if db_settings is None:
                return None
            db.expunge_all()
            return db_settings
