from sqlalchemy import Column, Integer, String
from monitorrent.db import DBSession, Base, get_engine


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


class SettingsManager(object):
    __password_settings_name = "monitorrent.password"
    __enable_authentication_settings_name = "monitorrent.is_authentication_enabled"

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

    def get_is_authentication_enabled(self):
        self.init_settings()
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == self.__enable_authentication_settings_name).first()
            if not setting:
                return True
            return setting.value == "True"

    def set_is_authentication_enabled(self, value):
        self.init_settings()
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == self.__enable_authentication_settings_name).first()
            if not setting:
                setting = Settings(name=self.__enable_authentication_settings_name)
                db.add(setting)
            setting.value = str(value)

    def enable_authentication(self):
        self.set_is_authentication_enabled(True)

    def disable_authentication(self):
        self.set_is_authentication_enabled(False)

    def init_settings(self):
        # Add default password
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == self.__password_settings_name).first()
            if not setting:
                setting = Settings(name=self.__password_settings_name, value='monitorrent')
                db.add(setting)
