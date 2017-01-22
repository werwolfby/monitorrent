from mock import Mock, ANY

from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import DBSession
from monitorrent.plugins.notifiers import NotifierType, Notifier, NotifierPlugin
from tests import DbTestCase


class NotifierMockSettings(Notifier):
    __tablename__ = "telegram_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)
    access_token = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'notifier_mock'
    }


class NotifierMock(NotifierPlugin):
    settings_fields = ['access_token']

    @property
    def get_type(self):
        return NotifierType.short_text

    def notify(self, header, body, url=None):
        pass

    @property
    def settings_class(self):
        return NotifierMockSettings


class TestUpdateSettings(DbTestCase):
    def test_empty_settings_should_delete_record_from_db(self):
        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN"))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN"

        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN1"))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN1"

        notifier.update_settings(NotifierMockSettings(access_token=None))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 0

        notifier.update_settings(NotifierMockSettings(access_token=""))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 0
