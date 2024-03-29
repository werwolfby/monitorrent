from __future__ import absolute_import
from builtins import range
from sqlalchemy import create_engine, event, Column, String, Integer, Table, types
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from datetime import datetime
import pytz


class ContextSession(sqlalchemy.orm.Session):
    """:class:`sqlalchemy.orm.Session` which can be used as context manager"""
    @property
    def dialect(self):
        return self.bind.dialect

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()


class UTCDateTime(types.TypeDecorator):

    impl = types.DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            return value.astimezone(pytz.utc)

    def process_result_value(self, value, engine):
        if value is not None:
            return datetime(value.year, value.month, value.day,
                            value.hour, value.minute, value.second,
                            value.microsecond, tzinfo=pytz.utc)

Base = declarative_base()
_DBSession = None
engine = None


def get_engine():
    return engine


def DBSession():
    return _DBSession()


def init_db_engine(connection_string, echo=False, **kwargs):
    global engine, _DBSession
    engine = create_engine(connection_string, echo=echo, **kwargs)

    # workaround for migrations on sqlite:
    # http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#pysqlite-serializable
    @event.listens_for(engine, 'connect')
    def do_connect(dbapi_connection, connection_record):
        # disable pysqlite's emitting of the BEGIN statement entirely.
        # also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def do_begin(conn):
        # emit our own BEGIN
        conn.execute("BEGIN")

    session_factory = sessionmaker(class_=ContextSession, bind=engine)
    _DBSession = scoped_session(session_factory)


def create_db():
    Base.metadata.create_all(engine)


def close_db():
    engine.dispose()


def row2dict(row, table=None, fields=None):
    """
    Converts SQLAlchemy row object or Table result into dict

    :rtype : dict
    """
    if table is not None:
        keys = list(table.columns.keys())
        return {keys[i]: row[i] for i in range(0, len(row))}

    return {name: getattr(row, name) for name in list(row._sa_class_manager.keys())
            if fields is None or name in fields}


def dict2row(row, data, fields=None):
    """
    :type fields: list
    :type data: dict
    """
    for k, v in list(data.items()):
        if hasattr(row, k) and ((fields is None) or k in fields) and not (fields is None and k.startswith('_')):
            setattr(row, k, v)


class MonitorrentOperations(Operations):
    def __init__(self, db, migration_context, impl=None):
        self.db = db
        super(MonitorrentOperations, self).__init__(migration_context, impl)

    def create_table(self, *args, **kw):
        if len(args) > 0 and type(args[0]) is Table:
            table = args[0]
            columns = [c.copy() for c in table.columns]
            if len(args) > 1:
                columns = columns + list(args[1:])
            return super(MonitorrentOperations, self).create_table(table.name, *columns, **kw)
        return super(MonitorrentOperations, self).create_table(*args, **kw)

    def has_table(self, name):
        return self.db.dialect.has_table(self.db, name)

    def upgrade_to_base_topic(self, v0, v1, polymorphic_identity, topic_mapping=None, column_renames=None):
        from .plugins import Topic

        self.create_table(v1)
        topics = self.db.query(v0)
        for topic in topics:
            raw_topic = row2dict(topic, v0)
            # insert into topics
            topic_values = {c: v for c, v in list(raw_topic.items()) if c in Topic.__table__.c and c != 'id'}
            topic_values['type'] = polymorphic_identity
            if topic_mapping:
                topic_mapping(topic_values, raw_topic)
            result = self.db.execute(Topic.__table__.insert(), topic_values)

            # get topic.id
            inserted_id = result.inserted_primary_key[0]

            # insert into v1 table
            concrete_topic = {c: v for c, v in list(raw_topic.items()) if c in v1.c}
            concrete_topic['id'] = inserted_id
            if column_renames:
                column_renames(concrete_topic, raw_topic)
            self.db.execute(v1.insert(), concrete_topic)
        # drop original table
        self.drop_table(v0.name)
        # rename new created table to old one
        self.rename_table(v1.name, v0.name)

    def __enter__(self):
        self.db.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.__exit__(exc_type, exc_val, exc_tb)
