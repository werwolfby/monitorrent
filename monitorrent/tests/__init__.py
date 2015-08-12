import os
import vcr
import vcr.cassette
import functools
import inspect
from unittest import TestCase
from sqlalchemy import Table, MetaData
from monitorrent.db import init_db_engine, close_db, DBSession, get_engine, MonitorrentOperations, MigrationContext
from monitorrent.plugins.trackers import Topic

test_vcr = vcr.VCR(
    cassette_library_dir=os.path.join(os.path.dirname(__file__), "cassettes"),
    record_mode="once"
)


def use_vcr(func=None, **kwargs):
    if func is None:
        # When called with kwargs, e.g. @use_vcr(inject_cassette=True)
        return functools.partial(use_vcr, **kwargs)
    if 'path' not in kwargs:
        module = func.__module__.split('tests.')[-1]
        class_name = inspect.stack()[1][3]
        cassette_name = '.'.join([module, class_name, func.__name__])
        kwargs.setdefault('path', cassette_name)
    return test_vcr.use_cassette(**kwargs)(func)


class UpgradeTestCase(TestCase):
    versions = []

    def setUp(self):
        init_db_engine("sqlite:///:memory:", echo=True)
        self.engine = get_engine()

    def tearDown(self):
        close_db()
        self.engine = None

    def has_table(self, table_name):
        return self.engine.dialect.has_table(self.engine.connect(), table_name)

    @staticmethod
    def operation_factory(session=None):
        if session is None:
            session = DBSession()
        migration_context = MigrationContext.configure(session)
        return MonitorrentOperations(session, migration_context)

    @staticmethod
    def copy(table, metadata):
        return Table(table.name, metadata, *[c.copy() for c in table.columns])

    def assertTable(self, expected_table):
        """
        :type expected_table: Table
        """
        m = MetaData(self.engine)
        table = Table(expected_table.name, m, autoload=True)
        self.assertEqual(len(expected_table.columns), len(table.columns))

        for column_name in expected_table.columns.keys():
            self.assertTrue(column_name in table.columns, 'Can\'t find column in table {}'.format(table.name))
            expected_column = expected_table.columns[column_name]
            column = table.columns[column_name]
            self.assertEqual(expected_column.primary_key, column.primary_key)
            self.assertEqual(expected_column.nullable, column.nullable)
            self.assertEqual(str(expected_column.type), str(column.type))

    def _upgrade(self):
        raise NotImplementedError()

    def _upgrade_from(self, topics, version):
        """
        :type topics: list[list] | None
        :type version: int
        """
        tables = self.versions[0 if version < 0 else version]
        tables[0].metadata.create_all(self.engine)
        if topics is not None:
            for i in reversed(range(len(topics))):
                table = tables[i]
                table_topics = topics[i]
                for topic in table_topics:
                    self.engine.execute(table.insert(), topic)

        self._upgrade()

        for table in tables:
            self.assertTrue(self.has_table(table.name))
        self.assertTrue(self.has_table(Topic.__tablename__))

        for table in self.versions[-1]:
            self.assertTable(table)
