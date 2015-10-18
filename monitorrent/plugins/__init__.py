from monitorrent.db import Base, UTCDateTime
from sqlalchemy import Column, Integer, String


class TopicPolymorphicMap(dict):
    base_mapper = None

    def __getitem__(self, key):
        if key not in self:
            return self.base_mapper
        return super(TopicPolymorphicMap, self).__getitem__(key)

    def __setitem__(self, key, value):
        if not self.base_mapper:
            self.base_mapper = value
        super(TopicPolymorphicMap, self).__setitem__(key, value)


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    last_update = Column(UTCDateTime, nullable=True)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'topic',
        'polymorphic_on': type,
        'with_polymorphic': '*',
        '_polymorphic_map': TopicPolymorphicMap()
    }
