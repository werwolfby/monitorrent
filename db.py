from sqlalchemy import create_engine
import sqlalchemy.orm
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base


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

def init_db_engine(connection_string, echo=False):
    engine = create_engine(connection_string, echo=echo)
    session_factory.configure(bind=engine)
    return engine

def create_db(engine):
    Base.metadata.create_all(engine)
