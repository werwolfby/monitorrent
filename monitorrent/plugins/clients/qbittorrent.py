from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import six

import requests
from io import BytesIO

from pytz import reference, utc
from sqlalchemy import Column, Integer, String

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
    REQUEST_FORMAT = "{0}:{1}/"

    def _get_params(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT

            try:
                session = requests.Session()
                target = self.REQUEST_FORMAT.format(cred.host, cred.port)
                payload = {"username": cred.username, "password": cred.password}
                response = session.post(target + "login",
                                        data=payload)
                if response.status_code != 200 or response.text == 'Fails.':
                    return False
                return {'session': session, 'target': target}
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
        return self._get_params()

    def find_torrent(self, torrent_hash):
        parameters = self._get_params()
        if not parameters:
            return False

        try:
            # qbittorrent uses case sensitive lower case hash
            torrent_hash = torrent_hash.lower()
            torrents = parameters['session'].get(parameters['target'] + "query/torrents")
            array = json.loads(torrents.text)
            torrent = next(torrent for torrent in array if torrent['hash'].lower() == torrent_hash)
            if torrent:
                time = torrent.get('addition_date', None)
                result_date = None
                if time is not None:
                    if isinstance(time, six.string_types):
                        result_date = dateutil.parser.parse(time).replace(tzinfo=reference.LocalTimezone())\
                            .astimezone(utc)
                    else:
                        result_date = datetime.fromtimestamp(time, utc)
                return {
                    "name": torrent['name'],
                    "date_added": result_date
                }
        except Exception as e:
            return False

    def get_download_dir(self):
        parameters = self._get_params()
        if not parameters:
            return None

        try:
            response = parameters['session'].get(parameters['target'] + 'query/preferences')
            response.raise_for_status()
            result = response.json()
            return six.text_type(result['save_path'])
        except:
            return None

    def add_torrent(self, torrent, torrent_settings):
        """
        :type torrent_settings: clients.TopicSettings | None
        """
        parameters = self._get_params()
        if not parameters:
            return False

        try:
            files = {"torrents": BytesIO(torrent)}
            data = None
            if torrent_settings is not None:
                data = {}
                if torrent_settings.download_dir is not None:
                    data['savepath'] = torrent_settings.download_dir
            r = parameters['session'].post(parameters['target'] + "command/upload", data=data, files=files)
            return r.status_code == 200
        except:
            return False

    # TODO switch to remove torrent with data
    def remove_torrent(self, torrent_hash):
        parameters = self._get_params()
        if not parameters:
            return False

        try:
            #qbittorrent uses case sensitive lower case hash
            torrent_hash = torrent_hash.lower()
            payload = {"hashes": torrent_hash}
            r = parameters['session'].post(parameters['target'] + "command/delete", data=payload)
            return r.status_code == 200
        except:
            return False

register_plugin('client', 'qbittorrent', QBittorrentClientPlugin())
