import six
import transmissionrpc
from pytz import reference, utc
from sqlalchemy import Column, Integer, String
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
import base64

from monitorrent.plugins.clients import DownloadStatus


class TransmissionCredentials(Base):
    __tablename__ = "transmission_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class TransmissionClientPlugin(object):
    name = "transmission"
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
    DEFAULT_PORT = 9091
    SUPPORTED_FIELDS = ['download_dir']

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
            cred.port = settings.get('port', self.DEFAULT_PORT)
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
                "date_added": torrent.date_added.replace(tzinfo=reference.LocalTimezone()).astimezone(utc)
            }
        except KeyError:
            return False

    def get_download_dir(self):
        client = self.check_connection()
        if not client:
            return None
        try:
            session = client.get_session()
            return six.text_type(session.download_dir)
        except:
            return None

    def add_torrent(self, torrent, torrent_settings):
        """
        :type torrent: str
        :type torrent_settings: clients.TopicSettings | None
        """
        client = self.check_connection()
        if not client:
            return False
        try:
            torrent_settings_dict = {}
            if torrent_settings is not None:
                if torrent_settings.download_dir is not None:
                    torrent_settings_dict['download_dir'] = torrent_settings.download_dir

            client.add_torrent(base64.b64encode(torrent).decode('utf-8'), **torrent_settings_dict)
            return True
        except transmissionrpc.TransmissionError:
            return False

    def remove_torrent(self, torrent_hash):
        client = self.check_connection()
        if not client:
            return False
        try:
            client.remove_torrent(torrent_hash.lower(), delete_data=False)
            return True
        except transmissionrpc.TransmissionError:
            return False

    def get_download_status(self, torrent_hash):
        client = self.check_connection()
        if not client:
            return False
        try:
            torrent = client.get_torrent(torrent_hash.lower(), ['id', 'hashString', 'totalSize', 'downloadedEver',
                                                                'rateDownload', 'rateUpload'])
            return DownloadStatus(torrent.downloadedEver, torrent.totalSize, torrent.rateDownload, torrent.rateUpload)
        except transmissionrpc.TransmissionError:
            return False


register_plugin('client', 'transmission', TransmissionClientPlugin())
