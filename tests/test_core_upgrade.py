from mock import Mock, patch, call
from sqlalchemy import Column, String, Integer, Table, MetaData
from monitorrent.db import DBSession
from monitorrent.upgrade_manager import core_upgrade, upgrade, _operation_factory
from tests import UpgradeTestCase


class CoreUpgradeTest(UpgradeTestCase):
    def upgrade_func(self, engine, operation_factory):
        pass

    def _upgrade(self):
        core_upgrade(self.operation_factory)

    def test_empty_db_test(self):
        self._test_empty_db_test()

    def test_not_existing_core_upgrade(self):
        core_upgrade(self.operation_factory)

    def test_empty_core_upgrade(self):
        m = MetaData()
        Table('plugin_versions', m,
              Column('plugin', String, nullable=False, primary_key=True),
              Column('version', Integer, nullable=False))

        m.create_all(self.engine)

        self._upgrade()

    def test_filled_core_upgrade(self):
        m = MetaData()
        versions = Table('plugin_versions', m,
                         Column('plugin', String, nullable=False, primary_key=True),
                         Column('version', Integer, nullable=False))

        m.create_all(self.engine)

        with DBSession() as db:
            db.execute(versions.insert(), {'plugin': 'lostfilm', 'version': -1})
            db.execute(versions.insert(), {'plugin': 'rutor', 'version': 2})

        self._upgrade()


class UpgradeTest(UpgradeTestCase):
    def upgrade_func(self, engine, operation_factory):
        pass

    def _upgrade(self):
        upgrade()

    def test_upgrade(self):
        core_upgrade_mock = Mock()
        call_ugprades_mock = Mock()
        upgrades_mock = ['test']
        with patch("monitorrent.upgrade_manager.core_upgrade", core_upgrade_mock), \
                patch("monitorrent.upgrade_manager.call_ugprades", call_ugprades_mock), \
                patch("monitorrent.upgrade_manager.upgrades", upgrades_mock):
            self._upgrade()

        core_upgrade_mock.assert_called_once_with(_operation_factory)
        call_ugprades_mock.assert_called_once_with(upgrades_mock)
