from pytest import raises

from sqlalchemy import Column, Integer, String, ForeignKey
from monitorrent.db import DBSession
from monitorrent.plugins.notifiers import NotifierType, Notifier, NotifierPlugin
from tests import DbTestCase


class NotifierMockSettings(Notifier):
    __tablename__ = "notifier_mock_settings"

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
    def test_is_enabled_should_be_set(self):
        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN"))
        assert notifier.is_enabled

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN"
            assert settings[0].is_enabled

        notifier.is_enabled = False
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN1"))
        assert not notifier.is_enabled

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN1"
            assert not settings[0].is_enabled

    def test_set_is_enabled_without_settings_shoud_throw(self):
        notifier = NotifierMock()
        assert not notifier.is_enabled

        with raises(Exception):
            notifier.is_enabled = False

    def test_first_set_settings_should_set_is_enabled_as_well(self):
        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN"))
        assert notifier.is_enabled

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN"
            assert settings[0].is_enabled

    def test_set_settings_on_disable_notifier_should_not_set_is_enabled(self):
        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN"))
        assert notifier.is_enabled

        notifier.is_enabled = False
        assert not notifier.is_enabled
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN1"))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN1"
            assert not settings[0].is_enabled

    def test_empty_settings_should_delete_record_from_db(self):
        notifier = NotifierMock()
        notifier.update_settings(NotifierMockSettings(access_token="TOKEN"))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 1
            assert settings[0].access_token == "TOKEN"
            assert settings[0].is_enabled

        notifier.update_settings(NotifierMockSettings(access_token=None))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 0

        notifier.update_settings(NotifierMockSettings(access_token=""))

        with DBSession() as db:
            settings = db.query(NotifierMockSettings).all()

            assert len(settings) == 0
