from __future__ import absolute_import, division, print_function, unicode_literals

import time
from datetime import datetime

import six
from pytz import utc
from qbittorrentapi import Client
from sqlalchemy import Column, Integer, String

from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.bittorrent_ex import Torrent


class QBittorrentCredentials(Base):
    __tablename__ = "qbittorrent_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class QBittorrentClientPlugin(object):
    name = "qbittorrent"
    form = [
        {
            "type": "row",
            "content": [
                {"type": "text", "label": "Host", "model": "host", "flex": 80},
                {"type": "text", "label": "Port", "model": "port", "flex": 20},
            ],
        },
        {
            "type": "row",
            "content": [
                {"type": "text", "label": "Username", "model": "username", "flex": 50},
                {
                    "type": "password",
                    "label": "Password",
                    "model": "password",
                    "flex": 50,
                },
            ],
        },
    ]
    DEFAULT_PORT = 8080
    SUPPORTED_FIELDS = ["download_dir"]
    ADDRESS_FORMAT = "{0}:{1}"

    def __init__(self):
        self._client = None

    def get_client(self):
        if not self._client:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                return None

            port = cred.port or self.DEFAULT_PORT
            address = self.ADDRESS_FORMAT.format(cred.host, port)

            return Client(host=address, username=cred.username, password=cred.password)

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                return None
            return {"host": cred.host, "port": cred.port, "username": cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                cred = QBittorrentCredentials()
                db.add(cred)
            cred.host = settings["host"]
            cred.port = settings.get("port", None)
            cred.username = settings.get("username", None)
            cred.password = settings.get("password", None)

    def check_connection(self):
        client = self.get_client()
        if not client:
            return False
        try:
            client.app_version()
            return True
        except Exception:
            return False

    def find_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        torrents = client.torrents_info(torrent_hashes=torrent_hash.lower())
        if torrents:
            torrent = torrents[0]
            result_date = datetime.fromtimestamp(torrent.added_on, utc)
            return {"name": torrent.name, "date_added": result_date}
        return False

    def get_download_dir(self):
        client = self.get_client()
        if not client:
            return None

        result = client.app_default_save_path()
        return six.text_type(result)

    def add_torrent(self, torrent_content, torrent_settings):
        client = self.get_client()
        if not client:
            return False

        kwargs = {}
        if torrent_settings and torrent_settings.download_dir:
            kwargs["save_path"] = torrent_settings.download_dir
            kwargs["use_auto_torrent_management"] = False

        result = client.torrents_add(torrent_files=torrent_content, **kwargs)

        if result == "Ok.":
            torrent = Torrent(torrent_content)
            torrent_hash = torrent.info_hash

            for _ in range(10):
                if self.find_torrent(torrent_hash):
                    return True
                time.sleep(1)
            return True

        return False

    def remove_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        client.torrents_delete(delete_files=False, torrent_hashes=torrent_hash.lower())
        return True


register_plugin("client", "qbittorrent", QBittorrentClientPlugin())
