from enum import Enum
from monitorrent.db import Base, UTCDateTime
from monitorrent.upgrade_manager import add_upgrade
from sqlalchemy import Column, Integer, Boolean, String, MetaData, Table
from sqlalchemy_enum34 import EnumType


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


class Status(Enum):
    Ok = 1,
    Error = 2,
    NotFound = 404,
    Unknown = 999

    @staticmethod
    def parse(name):
        names = {e.name.lower(): e for e in Status}
        return names[name.lower()]

    def __str__(self):
        if self == Status.Ok:
            return u"Ok"
        if self == Status.NotFound:
            return u"Not Found"
        if self == Status.Error:
            return u"Error"
        return u"Unknown"


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    display_name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False, unique=True)
    last_update = Column(UTCDateTime, nullable=True)
    type = Column(String)
    status = Column(EnumType(Status, by_name=True), nullable=False, server_default=Status.Ok.__str__())
    paused = Column(Boolean, nullable=False, server_default='0')

    __mapper_args__ = {
        'polymorphic_identity': 'topic',
        'polymorphic_on': type,
        'with_polymorphic': '*',
        '_polymorphic_map': TopicPolymorphicMap()
    }


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), Topic.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        with operations_factory() as operations:
            quality_column = Column('status', String(8), nullable=False, server_default=Status.Ok.__str__())
            operations.add_column(Topic.__tablename__, quality_column)
        version = 1
    if version == 1:
        with operations_factory() as operations:
            paused_column = Column('paused', Boolean, nullable=False, server_default='0')
            operations.add_column(Topic.__tablename__, paused_column)
        version = 2



def get_current_version(engine):
    m = MetaData(engine)
    topics = Table(Topic.__tablename__, m, autoload=True)
    if 'status' not in topics.columns:
        return 0
    if 'paused' not in topics.columns:
        return 1
    return 2


add_upgrade(upgrade)
