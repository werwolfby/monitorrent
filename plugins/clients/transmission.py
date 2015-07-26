import transmissionrpc
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from plugin_managers import register_plugin
import base64


class TransmissionCredentials(Base):
    __tablename__ = "transmission_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class TransmissionClientPlugin(object):
    name = "transmission"

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(TransmissionCredentials).first()
            if not cred:
                return None
            return {'host': cred.host, 'port': cred.port, 'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(TransmissionCredentials).first()
            if not cred:
                cred = TransmissionCredentials()
                db.add(cred)
            cred.host = settings['host']
            cred.port = settings['port']
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)

    def check_connection(self):
        with DBSession() as db:
            cred = db.query(TransmissionCredentials).first()
            if not cred:
                return False
            try:
                client = transmissionrpc.Client(address=cred.host, port=cred.port,
                                                user=cred.username, password=cred.password)
                return client
            except transmissionrpc.TransmissionError:
                return False

    def find_torrent(self, torrent_hash):
        client = self.check_connection()
        if not client:
            return False
        try:
            torrent = client.get_torrent(torrent_hash.lower(), ['id', 'hashString', 'addedDate', 'name'])
            return {
                "name": torrent.name,
                "date_added": torrent.date_added
            }
        except KeyError:
            return False

    def add_torrent(self, torrent):
        client = self.check_connection()
        if not client:
            return False
        client.add_torrent(base64.encodestring(torrent))
        return True

    def remove_torrent(self, torrent_hash):
        client = self.check_connection()
        if not client:
            return False
        client.remove_torrent(torrent_hash, delete_data=False)
        return True

register_plugin('client', 'transmission', TransmissionClientPlugin())
