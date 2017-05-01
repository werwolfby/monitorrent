from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from aenum import IntFlag

import requests
from io import BytesIO
from sqlalchemy import Column, Integer, String

from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.clients import DownloadStatus, TorrentDownloadStatus
from monitorrent.utils.soup import get_soup


class StatusFlags(IntFlag):
    Started = 1,
    Checking = 2,
    StartAfterCheck = 4,
    Checked = 8,
    Error = 16,
    Paused = 32,
    Queued = 64,
    Loaded = 128


def get_status(status):
    if StatusFlags.Error in status:
        return TorrentDownloadStatus.Error
    elif StatusFlags.Paused in status:
        return TorrentDownloadStatus.Paused
    elif StatusFlags.Started in status:
        return TorrentDownloadStatus.Downloading
    elif StatusFlags.Checking in status:
        return TorrentDownloadStatus.Checking
    elif StatusFlags.Queued in status:
        return TorrentDownloadStatus.Queued
    elif StatusFlags.Checked in status:
        return TorrentDownloadStatus.Paused



class UTorrentCredentials(Base):
    __tablename__ = "utorrent_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class UTorrentClientPlugin(object):
    name = "utorrent"
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
    SUPPORTED_FIELDS = []
    REQUEST_FORMAT = "{0}:{1}/gui/"

    def _get_params(self):
        with DBSession() as db:
            cred = db.query(UTorrentCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT

            try:
                session = requests.Session()
                session.auth = (cred.username, cred.password)
                target = self.REQUEST_FORMAT.format(cred.host, cred.port)
                response = session.get(target + "token.html",
                                       auth=(cred.username, cred.password))
                soup = get_soup(response.text)
                token = soup.div.text
                return {'session': session, 'target': target, 'token': token}
            except Exception as e:
                return False

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(UTorrentCredentials).first()
            if not cred:
                return None
            return {'host': cred.host, 'port': cred.port, 'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(UTorrentCredentials).first()
            if not cred:
                cred = UTorrentCredentials()
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

        payload = {"list": '1', "token": parameters["token"]}
        torrents = parameters['session'].get(parameters['target'],
                                             params=payload)
        array = json.loads(torrents.text)['torrents']
        torrent = next(torrent for torrent in array if torrent[0] == torrent_hash)
        if torrent:
            return {
                "name": torrent[2],
                # date added not supported by web api
                "date_added": None
            }

    def add_torrent(self, torrent, torrent_settings):
        parameters = self._get_params()
        if not parameters:
            return False

        payload = {"action": "add-file", "token": parameters["token"]}
        files = {"torrent_file": BytesIO(torrent)}
        r = parameters['session'].post(parameters['target'], params=payload, files=files)
        return r.status_code == 200

    # TODO switch to remove torrent with data
    def remove_torrent(self, torrent_hash):
        parameters = self._get_params()
        if not parameters:
            return False

        payload = {"action": "remove", "hash": torrent_hash, "token": parameters["token"]}
        parameters['session'].get(parameters['target'], params=payload)
        return True

    def get_download_status(self):
        parameters = self._get_params()
        payload = {"list": '1', "token": parameters["token"]}
        torrents = parameters['session'].get(parameters['target'],
                                             params=payload)
        array = json.loads(torrents.text)['torrents']
        result = {}
        for torrent in array:
            result[torrent[0]] = DownloadStatus(torrent[5], torrent[3], torrent[9], torrent[8],
                                                get_status(StatusFlags(torrent[1])),
                                                float(torrent[4]) / 10.0, torrent[7])
        return result

    def get_download_status_by_hash(self, torrent_hash):
        parameters = self._get_params()

        payload = {"list": '1', "token": parameters["token"]}
        torrents = parameters['session'].get(parameters['target'],
                                             params=payload)
        array = json.loads(torrents.text)['torrents']
        torrent = next(torrent for torrent in array if torrent[0] == torrent_hash)
        if torrent:
            return DownloadStatus(torrent[5], torrent[3], torrent[9], torrent[8], get_status(StatusFlags(torrent[1])),
                                  float(torrent[4]) / 10.0, torrent[7])


register_plugin('client', 'utorrent', UTorrentClientPlugin())
