from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import six

import tempfile

from pytz import reference, utc
from sqlalchemy import Column, Integer, String

from qbittorrentapi import Client

from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from datetime import datetime
import dateutil.parser


class QBittorrentCredentials(Base):
    __tablename__ = "qbittorrent_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class QBittorrentClientPlugin(object):
    name = "qbittorrent"
    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Host',
            'model': 'host',
            'flex': 80
        }, {
            'type': 'text',
            'label': 'Port',
            'model': 'port',
            'flex': 20
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Username',
            'model': 'username',
            'flex': 50
        }, {
            'type': 'password',
            'label': 'Password',
            'model': 'password',
            'flex': 50
        }]
    }]
    DEFAULT_PORT = 8080
    SUPPORTED_FIELDS = ['download_dir']
    ADDRESS_FORMAT = "{0}:{1}"

    def _get_client(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT

            address = self.ADDRESS_FORMAT.format(cred.host, cred.port)

            client = Client(host=address, username=cred.username, password=cred.password)
            client.app_version()
            return client
        
    def get_settings(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                return None
            return {'host': cred.host, 'port': cred.port, 'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                cred = QBittorrentCredentials()
                db.add(cred)
            cred.host = settings['host']
            cred.port = settings.get('port', None)
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)

    def check_connection(self):
        return self._get_client()

    def find_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False

        torrents = client.torrents_info(hashes=[torrent_hash.lower()])
        if torrents:
            time = torrents[0].info.added_on
            result_date = datetime.fromtimestamp(time, utc)
            return {
                "name": torrents[0].name,
                "date_added": result_date
            }
        return False

    def get_download_dir(self):
        client = self._get_client()
        if not client:
            return None

        result = client.app_default_save_path()
        return six.text_type(result)

    def add_torrent(self, torrent, torrent_settings):
        """
        :type torrent_settings: clients.TopicSettings | None
        """
        client = self._get_client()
        if not client:
            return False

        savepath = None
        if torrent_settings is not None and torrent_settings.download_dir is not None:
            savepath = torrent_settings.download_dir

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(torrent)
            tmp.flush()
            r = client.torrents_add(save_path=savepath, torrent_files=[tmp.name])
            return r

    def remove_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False

        client.torrents_delete(hashes=[torrent_hash.lower()])
        return True


register_plugin('client', 'qbittorrent', QBittorrentClientPlugin())
