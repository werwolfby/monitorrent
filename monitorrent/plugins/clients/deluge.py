import six
import base64
from deluge_client import DelugeRPCClient
import pytz
from sqlalchemy import Column, Integer, String
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from datetime import datetime

from monitorrent.plugins.clients import DownloadStatus


class DelugeCredentials(Base):
    __tablename__ = "deluge_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class DelugeClientPlugin(object):
    name = "deluge"
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
    DEFAULT_PORT = 58846
    SUPPORTED_FIELDS = ['download_dir']

    def get_settings(self):
        with DBSession() as db:
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
            cred.port = settings.get('port', None)
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)

    def _get_client(self):
        with DBSession() as db:
            cred = db.query(DelugeCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT
            return DelugeRPCClient(cred.host, cred.port, cred.username, cred.password)

    def check_connection(self):
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
            return client.connected
        except:
            return False

    def get_download_dir(self):
        client = self._get_client()
        if not client:
            return None
        try:
            client.connect()
            return client.call('core.get_config_value', 'move_completed_path').decode('utf-8')
        except:
            return None

    def find_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
        except:
            return False
        torrent = client.call("core.get_torrent_status",
                              torrent_hash.lower(), ['time_added', 'name'])
        if len(torrent) == 0:
            return False
        # time_added return time in local timezone, so lets convert it to UTC
        return {
            "name": torrent[b'name'].decode('utf-8'),
            "date_added": datetime.utcfromtimestamp(torrent[b'time_added']).replace(tzinfo=pytz.utc)
        }

    def add_torrent(self, torrent, torrent_settings):
        # TODO add path to download
        # path_to_download = None
        """

        :type torrent_settings: clients.TopicSettings
        """
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
            options = None
            if torrent_settings is not None:
                options = {}
                if torrent_settings.download_dir is not None:
                    options['download_location'] = torrent_settings.download_dir
            return client.call("core.add_torrent_file",
                               None, base64.b64encode(torrent), options)
        except:
            return False

    def remove_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
            return client.call("core.remove_torrent",
                               torrent_hash.lower(), False)
        except:
            return False

    def get_download_status(self, torrent_hash):
        client = self._get_client()
        lower_hash = torrent_hash.lower()
        if not client:
            return False
        try:
            client.connect()
            result = client.call("core.get_torrents_status",
                                 {'hash': lower_hash}, ['total_done', 'total_size', 'download_payload_rate',
                                                                  'upload_payload_rate', 'state', 'progress'])
            key, value = result.popitem()
            return DownloadStatus(value[b'total_done'], value[b'total_size'],
                                  value[b'download_payload_rate'], value[b'upload_payload_rate'])
        except:
            return False


register_plugin('client', 'deluge', DelugeClientPlugin())
