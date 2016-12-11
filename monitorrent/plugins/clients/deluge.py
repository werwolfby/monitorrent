from builtins import object
import base64
from deluge_client import DelugeRPCClient
import pytz
from sqlalchemy import Column, Integer, String
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from datetime import datetime


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
            "name": torrent['name'],
            "date_added": datetime.utcfromtimestamp(torrent['time_added']).replace(tzinfo=pytz.utc)
        }

    def add_torrent(self, torrent, torrent_settings):
        # TODO add path to download
        # path_to_download = None
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
            return client.call("core.add_torrent_file",
                               None, base64.encodebytes(torrent), None)
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


register_plugin('client', 'deluge', DelugeClientPlugin())
