from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = sessionmaker()

def init_db_engine(connection_string, echo=False):
    engine = create_engine(connection_string, echo=echo)
    Session.configure(bind=engine)
    return engine

def create_db(engine):
    Base.metadata.create_all(engine)
