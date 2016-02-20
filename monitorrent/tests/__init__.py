import abc
import os
import vcr
import vcr.cassette
import functools
import inspect
import codecs
from unittest import TestCase
from sqlalchemy import Table, MetaData
from sqlalchemy.pool import StaticPool
from monitorrent.db import init_db_engine, create_db, close_db, DBSession, get_engine
from monitorrent.upgrade_manager import call_ugprades, MonitorrentOperations, MigrationContext
from monitorrent.plugins.trackers import Topic
from monitorrent.rest import create_api, AuthMiddleware
from falcon.testing import TestBase

tests_dir = os.path.dirname(os.path.realpath(__file__))
httpretty_dir = os.path.join(tests_dir, 'httprety')
cassette_library_dir = os.path.join(tests_dir, "cassettes")

test_vcr = vcr.VCR(
    cassette_library_dir=cassette_library_dir,
    record_mode="once"
)


def use_vcr(func=None, **kwargs):
    if func is None:
        # When called with kwargs, e.g. @use_vcr(inject_cassette=True)
        return functools.partial(use_vcr, **kwargs)
    if 'path' not in kwargs:
        module = func.__module__.split('tests.')[-1].split('.')[-1]
        class_name = inspect.stack()[1][3]
        cassette_name = '.'.join([module, class_name, func.__name__])
        kwargs.setdefault('path', cassette_name)
    return test_vcr.use_cassette(**kwargs)(func)


class DbTestCase(TestCase):
    def setUp(self):
        init_db_engine("sqlite://", echo=False,
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
        create_db()
        self.engine = get_engine()

    def tearDown(self):
        close_db()
        self.engine = None

    def has_table(self, table_name):
        with self.engine.connect() as c:
            return self.engine.dialect.has_table(c, table_name)


class ReadContentMixin(object):
    @staticmethod
    def read_content(file_name, mode='r', encoding=None):
        with codecs.open(os.path.join(tests_dir, file_name), mode=mode, encoding=encoding) as f:
            return f.read()

    @staticmethod
    def read_httpretty_content(file_name, mode='r', encoding=None):
        return ReadContentMixin.read_content(os.path.join('httprety', file_name), mode, encoding)


class TestGetCurrentVersionMeta(type):
    def __new__(mcs, name, bases, attrs):
        """
        :type mcs: UpgradeTestCase
        """

        def gen_test(version):
            def test(self):
                self.get_current_version_test(version)
            return test

        if 'versions' in attrs and len(attrs['versions']) > 0:
            for v in range(0, len(attrs['versions'])):
                test_name = "test_get_current_version_%s" % v
                attrs[test_name] = gen_test(v)
        return type.__new__(mcs, name, bases, attrs)


class UpgradeTestCase(DbTestCase):
    __metaclass__ = TestGetCurrentVersionMeta
    versions = []

    @abc.abstractmethod
    def upgrade_func(self, engine, operation_factory):
        """
        """

    def setUp(self):
        init_db_engine("sqlite:///:memory:", echo=False)
        self.engine = get_engine()

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

    def _test_empty_db_test(self):
        self._upgrade()
        m = MetaData()
        m.reflect(self.engine)
        self.assertEqual(0, len(m.tables))

    def get_current_version_test(self, version):
        if hasattr(self, '_get_current_version'):
            tables = self.versions[version]
            tables[0].metadata.create_all(self.engine)
            self.assertEqual(version, self._get_current_version())
        else:
            self.skipTest('_get_current_version is not specified')

    def _upgrade(self):
        call_ugprades([self.upgrade_func])

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


class RestTestBase(TestBase):
    @classmethod
    def setUpClass(cls):
        super(RestTestBase, cls).setUpClass()
        AuthMiddleware.init('secret!', 'monitorrent', None)
        cls.auth_token_verified = 'eyJhbGciOiJIUzI1NiJ9.Im1vbml0b3JyZW50Ig.95p-fZYKe6CjaUbf7-gw2JKXifsocYf0w52rj-U7vHw'
        cls.auth_token_tampared = 'eyJhbGciOiJIUzI1NiJ9.Im1vbml0b3JyZW5UIg.95p-fZYKe6CjaUbf7-gw2JKXifsocYf0w52rj-U7vHw'

    def setUp(self, disable_auth=True):
        super(RestTestBase, self).setUp()
        self.api = create_api(disable_auth=disable_auth)

    def get_cookie(self, modify=False):
        token = self.auth_token_tampared if modify else self.auth_token_verified
        if modify:
            token = token
        return AuthMiddleware.cookie_name + '=' + token + '; HttpOnly; Path=/'
