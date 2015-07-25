import base64
from deluge_client import DelugeRPCClient
from sqlalchemy import Column, Integer, String
from db import Base, DBSession
from plugin_managers import register_plugin
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

            deluge_port = "58846"
            if not cred.port:
                cred.port = deluge_port
            return DelugeRPCClient(cred.host, cred.port, cred.username, cred.password)

    def check_connection(self):
        client = self._get_client()
        if not client:
            return False
        try:
            client.connect()
            return client.connected
        except Exception:
            return False

    def find_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False
        client.connect()
        torrent = client.call("core.get_torrent_status",
                              torrent_hash.lower(), ['time_added', 'name'])
        if len(torrent) == 0:
            return False
        return {
            "name": torrent['name'],
            "date_added": datetime.fromtimestamp(torrent['time_added'])
        }

    # TODO add path to download
    def add_torrent(self, torrent):
        path_to_download = None
        client = self._get_client()
        if not client:
            return False
        client.connect()
        result = client.call("core.add_torrent_file",
                             None, base64.encodestring(torrent), None)
        return result

    def remove_torrent(self, torrent_hash):
        client = self._get_client()
        if not client:
            return False
        client.connect()
        try:
            return client.call("core.remove_torrent",
                               torrent_hash.lower(), False)
        except:
            return False


register_plugin('client', 'deluge', DelugeClientPlugin())
