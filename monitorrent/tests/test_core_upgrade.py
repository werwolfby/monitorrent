from sqlalchemy import Column, String, Integer, Table, MetaData
from monitorrent.db import core_upgrade, DBSession
from monitorrent.tests import UpgradeTestCase


class CoreUpgradeTest(UpgradeTestCase):
    def test_not_existing_core_upgrade(self):
        core_upgrade(self.engine, self.operation_factory)

    def test_empty_core_upgrade(self):
        m = MetaData()
        Table('plugin_versions', m,
              Column('plugin', String, nullable=False, primary_key=True),
              Column('version', Integer, nullable=False))

        m.create_all(self.engine)

        core_upgrade(self.engine, self.operation_factory)

    def test_filled_core_upgrade(self):
        m = MetaData()
        versions = Table('plugin_versions', m,
                         Column('plugin', String, nullable=False, primary_key=True),
                         Column('version', Integer, nullable=False))

        m.create_all(self.engine)

        with DBSession() as db:
            db.execute(versions.insert(), {'plugin': 'lostfilm', 'version': -1})
            db.execute(versions.insert(), {'plugin': 'rutor', 'version': 2})

        core_upgrade(self.engine, self.operation_factory)
