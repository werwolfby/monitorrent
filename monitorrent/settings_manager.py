from builtins import str
from builtins import object
from sqlalchemy import Column, Integer, String
from monitorrent.db import DBSession, Base
from monitorrent.plugins.trackers import TrackerSettings


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


class SettingsManager(object):
    __password_settings_name = "monitorrent.password"
    __enable_authentication_settings_name = "monitorrent.is_authentication_enabled"
    __default_client_settings_name = "monitorrent.default_client"
    __developer_mode_settings_name = "monitorrent.developer_mode"
    __requests_timeout = "monitorrent.requests_timeout"
    __remove_logs_interval_settings_name = "monitorrent.remove_logs_interval"
    __proxy_enabled_name = "monitorrent.proxy_enabled"
    __proxy_id_format = "monitorrent.proxy_{0}"

    def get_password(self):
        return self._get_settings(self.__password_settings_name, 'monitorrent')

    def set_password(self, value):
        self._set_settings(self.__password_settings_name, value)

    def get_is_authentication_enabled(self):
        return self._get_settings(self.__enable_authentication_settings_name, 'True') == 'True'

    def set_is_authentication_enabled(self, value):
        self._set_settings(self.__enable_authentication_settings_name, str(value))

    def enable_authentication(self):
        self.set_is_authentication_enabled(True)

    def disable_authentication(self):
        self.set_is_authentication_enabled(False)

    def get_default_client(self):
        return self._get_settings(self.__default_client_settings_name)

    def set_default_client(self, value):
        self._set_settings(self.__default_client_settings_name, value)

    def get_is_developer_mode(self):
        return self._get_settings(self.__developer_mode_settings_name) == 'True'

    def set_is_developer_mode(self, value):
        self._set_settings(self.__developer_mode_settings_name, str(value))

    def get_is_proxy_enabled(self):
        return self._get_settings(self.__proxy_enabled_name) == 'True'

    def set_is_proxy_enabled(self, value):
        self._set_settings(self.__proxy_enabled_name, str(value))

    def get_proxy(self, index):
        proxy_name = self.__proxy_id_format.format(index)
        return self._get_settings(proxy_name)

    def set_proxy(self, index, value):
        proxy_name = self.__proxy_id_format.format(index)
        if value == None:
            self._remove_settings(proxy_name)
        else:
            self._set_settings(proxy_name, value)

    @property
    def requests_timeout(self):
        return float(self._get_settings(self.__requests_timeout, 10))

    @requests_timeout.setter
    def requests_timeout(self, value):
        self._set_settings(self.__requests_timeout, str(value))

    @property
    def tracker_settings(self):
        return TrackerSettings(self.requests_timeout)

    @tracker_settings.setter
    def tracker_settings(self, value):
        self.requests_timeout = value.requests_timeout

    @property
    def remove_logs_interval(self):
        return int(self._get_settings(self.__remove_logs_interval_settings_name, 10))

    @remove_logs_interval.setter
    def remove_logs_interval(self, value):
        self._set_settings(self.__remove_logs_interval_settings_name, str(value))

    @staticmethod
    def _get_settings(name, default=None):
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == name).first()
            if not setting:
                return default
            # this is right convert from string to bool
            return setting.value or default

    @staticmethod
    def _set_settings(name, value):
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == name).first()
            if not setting:
                setting = Settings(name=name)
                db.add(setting)
            setting.value = str(value)

    @staticmethod
    def _remove_settings(name):
        with DBSession() as db:
            setting = db.query(Settings).filter(Settings.name == name).first()
            if not setting:
                return
            db.delete(setting)
