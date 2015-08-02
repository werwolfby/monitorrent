from db import Base
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    last_update = Column(DateTime, nullable=True)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'topic',
        'polymorphic_on': type,
        'with_polymorphic': '*'
    }
