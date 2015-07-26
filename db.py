from sqlalchemy import create_engine, Column, String, Integer
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from alembic.migration import MigrationContext
from alembic.operations import Operations


class ContextSession(sqlalchemy.orm.Session):
    """:class:`sqlalchemy.orm.Session` which can be used as context manager"""
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

Base = declarative_base()
session_factory = sessionmaker(class_=ContextSession)
DBSession = scoped_session(session_factory)
engine = None


def init_db_engine(connection_string, echo=False):
    global engine
    engine = create_engine(connection_string, echo=echo)
    session_factory.configure(bind=engine)

def create_db():
    Base.metadata.create_all(engine)

def row2dict(row):
    """
    Converts SQLAlchemy row object into dict

    :rtype : dict
    """
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}

CoreBase = declarative_base()


class Version(CoreBase):
    __tablename__ = 'plugin_versions'

    plugin = Column(String, nullable=False, primary_key=True)
    version = Column(Integer, nullable=False)


def get_version(name):
    with DBSession() as db:
        version = db.query(Version).filter(Version.plugin == name).first()
        if not version:
            return -1
        return version.version

def set_version(name, version):
    with DBSession() as db:
        db_version = db.query(Version).filter(Version.plugin == name).first()
        if not db_version:
            db_version = Version(plugin=name)
            db.add(db_version)
        db_version.version = version
        db.commit()

def upgrade(plugins, upgrades):
    CoreBase.metadata.create_all(engine)

    migration_context = MigrationContext.configure(engine)
    operations = Operations(migration_context)

    for name, plugins in plugins.items():
        upgrade_func = upgrades.get(name, None)
        if not upgrade_func:
            continue
        version = get_version(name)
        try:
            version = upgrade_func(engine, operations, version)
            set_version(name, version)
        except Exception as e:
            print e
