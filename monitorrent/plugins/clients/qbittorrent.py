from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
import time

from pytz import utc
from sqlalchemy import Column, Integer, String

from qbittorrentapi import Client

from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.bittorrent_ex import Torrent
from datetime import datetime


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
    _client = None

    def get_client(self):
        if not self._client:
            self._client = self._get_client()
        return self._client

    def _get_client(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT

            try:
                address = self.ADDRESS_FORMAT.format(cred.host, cred.port)

                client = Client(host=address, username=cred.username, password=cred.password)
                client.app_version()
                return QBittorrentClientPlugin._decorate_post(client)
            except Exception as e:
                return False

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
        try:
            client = self.get_client()
            client.app_version()
            return True
        except:
            return False

    def find_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        try:
            torrents = client.torrents_info(hashes=[torrent_hash.lower()])
            if torrents:
                time = torrents[0].info.added_on
                result_date = datetime.fromtimestamp(time, utc)
                return {
                    "name": torrents[0].name,
                    "date_added": result_date
                }
            return False
        except Exception as e:
            return False

    def get_download_dir(self):
        client = self.get_client()
        if not client:
            return None

        try:
            result = client.app_default_save_path()
            return six.text_type(result)
        except:
            return None

    def add_torrent(self, torrent_content, torrent_settings):
        """
        :type torrent_settings: clients.TopicSettings | None
        """
        client = self.get_client()
        if not client:
            return False

        try:
            savepath = None
            auto_tmm = None
            if torrent_settings is not None and torrent_settings.download_dir is not None:
                savepath = torrent_settings.download_dir
                auto_tmm = False

            res = client.torrents_add(save_path=savepath, use_auto_torrent_management=auto_tmm, torrent_contents=[('file.torrent', torrent_content)])
            if 'Ok' in res:
                torrent = Torrent(torrent_content)
                torrent_hash = torrent.info_hash
                for i in range(0, 10):
                    found = self.find_torrent(torrent_hash)
                    if found:
                        return True
                    time.sleep(1)

            return False
        except:
            return False

    def remove_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        try:
            client.torrents_delete(hashes=[torrent_hash.lower()])
            return True
        except:
            return False

    @staticmethod
    def _decorate_post(client):
        def _post_decorator(func):
            def _post_wrapper(*args, **kwargs):
                if 'torrent_contents' in kwargs:
                    kwargs['files'] = kwargs['torrent_contents']
                    del kwargs['torrent_contents']
                return func(*args, **kwargs)
            return _post_wrapper

        client._post = _post_decorator(client._post)
        return client


register_plugin('client', 'qbittorrent', QBittorrentClientPlugin())
