from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
session_factory = sessionmaker()
Session = scoped_session(session_factory)

def init_db_engine(connection_string, echo=False):
    engine = create_engine(connection_string, echo=echo)
    session_factory.configure(bind=engine)
    return engine

def create_db(engine):
    Base.metadata.create_all(engine)
