from builtins import str
from builtins import object
from enum import Enum

from sqlalchemy import Column, Integer, String
from monitorrent.db import DBSession, Base, row2dict
from monitorrent.plugins.trackers import TrackerSettings


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


class ProxySettings(Base):
    __tablename__ = 'settings_proxy'

    key = Column(String, primary_key=True)
    url = Column(String, nullable=False)


class NotificationLevel(Enum):
    ERROR = 1,
    NOT_FOUND = 2,
    UPDATED = 3



class SettingsManager(object):
    __password_settings_name = "monitorrent.password"
    __enable_authentication_settings_name = "monitorrent.is_authentication_enabled"
    __default_client_settings_name = "monitorrent.default_client"
    __developer_mode_settings_name = "monitorrent.developer_mode"
    __requests_timeout = "monitorrent.requests_timeout"
    __remove_logs_interval_settings_name = "monitorrent.remove_logs_interval"
    __proxy_enabled_name = "monitorrent.proxy_enabled"
    __proxy_id_format = "monitorrent.proxy_{0}"
    __new_version_checker_enabled = "monitorrent.new_version_checker_enabled"
    __new_version_check_include_prerelease = "monitorrent.new_version_check_include_prerelease"
    __new_version_check_interval = "monitorrent.new_version_check_interval"
    __external_notifications_level_settings_name = "monitorrent.external_notifications_level"

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

    def get_external_notifications_levels(self):
        levels = self._get_settings(self.__external_notifications_level_settings_name, "ERROR,NOT_FOUND,UPDATED")
        if levels is None:
            return None
        else:
            return levels.split(",")

    def set_external_notifications_levels(self, values):
        if values is None:
            self._set_settings(self.__external_notifications_level_settings_name, None)
        else:
            self._set_settings(self.__external_notifications_level_settings_name, ",".join(values))

    def get_is_proxy_enabled(self):
        return self._get_settings(self.__proxy_enabled_name) == 'True'

    def set_is_proxy_enabled(self, value):
        self._set_settings(self.__proxy_enabled_name, str(value))

    def get_proxy(self, key):
        with DBSession() as db:
            setting = db.query(ProxySettings).filter(ProxySettings.key == key).first()
            if setting is None:
                return None
            return setting.url

    def set_proxy(self, key, url):
        with DBSession() as db:
            setting = db.query(ProxySettings).filter(ProxySettings.key == key).first()
            if url is not None and url != "":
                if setting is None:
                    setting = ProxySettings(key=key)
                setting.url = url
                db.add(setting)
            else:
                if setting is None:
                    return
                db.delete(setting)

    def get_proxies(self):
        with DBSession() as db:
            settings = db.query(ProxySettings).all()
            return {s.key: s.url for s in settings}

    def get_is_new_version_checker_enabled(self):
        return self._get_settings(self.__new_version_checker_enabled, 'True') == 'True'

    def set_is_new_version_checker_enabled(self, value):
        self._set_settings(self.__new_version_checker_enabled, str(value))

    def get_new_version_check_include_prerelease(self):
        return self._get_settings(self.__new_version_check_include_prerelease, 'False') == 'True'

    def set_new_version_check_include_prerelease(self, value):
        self._set_settings(self.__new_version_check_include_prerelease, str(value))

    @property
    def new_version_check_interval(self):
        return int(self._get_settings(self.__new_version_check_interval, 3600))

    @new_version_check_interval.setter
    def new_version_check_interval(self, value):
        self._set_settings(self.__new_version_check_interval, str(value))

    @property
    def requests_timeout(self):
        return float(self._get_settings(self.__requests_timeout, 10))

    @requests_timeout.setter
    def requests_timeout(self, value):
        self._set_settings(self.__requests_timeout, str(value))

    @property
    def tracker_settings(self):
        proxy_enabled = self.get_is_proxy_enabled()
        return TrackerSettings(self.requests_timeout, self.get_proxies() if proxy_enabled else None)

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
