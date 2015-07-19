import json
import requests
from sqlalchemy import Column, Integer, String
import subprocess
from db import Base, DBSession
from plugin_managers import register_plugin


class DelugeCredentials(Base):
    __tablename__ = "deluge_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    deluge_console_executable = Column(String, nullable=True)


class DelugeClientPlugin(object):
    name = "deluge"

    def get_settings(self):
        with DBSession as db:
            cred = db.query(DelugeCredentials).first()
            if not cred:
                return None
            return {'host': cred.host, 'port': cred.port, 'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(DelugeCredentials).first()
            if not cred:
                cred = DelugeCredentials()
                db.add(cred)
            cred.host = settings['host']
            cred.port = settings['port']
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)

    def _get_creds(self):
        with DBSession() as db:
            cred = db.query(DelugeCredentials).first()

        if not cred:
            return False

            # deluge_executable = "deluge-console"
        deluge_executable = "C:\\Program Files (x86)\\Deluge\\deluge-console.exe"
        if cred.deluge_console_executable:
            cred.deluge_console_executable = deluge_executable
        deluge_port = "58846"
        if cred.port:
            cred.port = deluge_port
        return cred

    def check_connection(self):
        cred = self._get_creds()
        if not cred:
            return False;

        parameters = "connect {}:{} {} {}; info --sort=active_time".format(cred.host,
                                                                           cred.port,
                                                                           cred.username,
                                                                           cred.password)
        try:
            return subprocess.check_output([cred.deluge_console_executable, parameters], timeout=10)
        except Exception:
            return False

    def add_torrent(self, torrent, path_to_download):
        cred = self._get_creds()
        if not cred:
            return False
        parameters = "connect {}:{} {} {}; add ".format(cred.host,
                                                        cred.port,
                                                        cred.username,
                                                        cred.password)
        if path_to_download:
            parameters += "-p {}".format(
                path_to_download
            )
        parameters += torrent
        try:
            return subprocess.check_output([cred.deluge_console_executable, parameters], timeout=10) == "Torrent added!"
        except Exception:
            return False
        return True

    def remote_torrent(self, torrent_hash):
        cred = self._get_creds()
        if not cred:
            return False

        # TODO this could be an optional parameter to remove torrent data
        del_opt = "--remove_data"
        parameters = "connect {}:{} {} {}; re {}".format(cred.host,
                                                         cred.port,
                                                         cred.username,
                                                         cred.password,
                                                         torrent_hash)
        try:
            return subprocess.check_output([cred.deluge_console_executable, parameters], timeout=10)
        except Exception:
            return False
        return True


register_plugin('client', 'deluge', DelugeClientPlugin())
