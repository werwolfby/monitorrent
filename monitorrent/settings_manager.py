from sqlalchemy import Column, Integer, String
from monitorrent.db import DBSession, Base, get_engine


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


class SettingsManager(object):
    __password_settings_name = "monitorrent.password"

    def __init__(self):
        engine = get_engine()
        self.settings_exist = engine.dialect.has_table(engine.connect(), Settings.__tablename__)

    def get_password(self):
        self.init_settings()
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == self.__password_settings_name).first()
            if not setting:
                return None
            return setting.value

    def set_password(self, value):
        self.init_settings()
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == self.__password_settings_name).first()
            if not setting:
                setting = Settings(name=self.__password_settings_name)
                db.add(setting)
            setting.value = value

    def init_settings(self):
        if self.settings_exist:
            return

        try:
            # Add default password
            with DBSession() as db:
                setting = Settings(name=self.__password_settings_name, value="monitorrent")
                db.add(setting)
        finally:
            self.settings_exist = True
