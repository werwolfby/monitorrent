import pytz
from monitorrent.db import UTCDateTime
from monitorrent.plugins.notifiers.telegram import upgrade, get_current_version
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from datetime import datetime
from tests import UpgradeTestCase
from monitorrent.plugins.trackers import Topic


class TelegramNotifierUpgradeTest(UpgradeTestCase):
    m0 = MetaData()
    TelegramSettings0 = Table('telegram_settings', m0,
                              Column('id', Integer, primary_key=True),
                              Column('chat_id', Integer, nullable=True),
                              Column('access_token', String, nullable=True))

    m1 = MetaData()
    TelegramSettings1 = Table('telegram_settings', m1,
                              Column('id', Integer, primary_key=True),
                              Column('chat_ids', String, nullable=True),
                              Column('access_token', String, nullable=True))

    versions = [
        (TelegramSettings0, ),
        (TelegramSettings1, )
    ]

    def upgrade_func(self, engine, operation_factory):
        upgrade(engine, operation_factory)

    def _get_current_version(self):
        return get_current_version(self.engine)

    def test_empty_db_test(self):
        self._test_empty_db_test()

    def test_updage_empty_from_version_0(self):
        self._upgrade_from(None, 0)

    def test_updage_empty_from_version_1(self):
        self._upgrade_from(None, 1)

    def test_updage_filled_from_version_0(self):
        credential = {'chat_id': 12345, 'access_token': 'bot_is_fake'}

        self._upgrade_from([[credential]], 0)

        settings = list(self.engine.execute(self.TelegramSettings1.select()))

        assert len(settings) == 1
        assert settings[0].chat_ids == '12345'
        assert settings[0].access_token == 'bot_is_fake'
