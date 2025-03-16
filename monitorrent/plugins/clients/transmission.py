import six
import transmissionrpc
from pytz import reference, utc
from sqlalchemy import Column, Integer, String
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
import base64

class TransmissionCredentials(Base):
    __tablename__ = "transmission_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    download_dir = Column(String, nullable=True)  # Новое поле

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
    }, {
        'type': 'text',
        'label': 'Download Directory',
        'model': 'download_dir',
        'placeholder': 'Leave empty to use default'
    }]
    DEFAULT_PORT = 9091
    SUPPORTED_FIELDS = ['download_dir']

    def get_settings(self):
        with db_session() as db:
            cred = db.query(TransmissionCredentials).first()
            if not cred:
                return None
            return {
                'host': cred.host,
                'port': cred.port,
                'username': cred.username,
                'download_dir': cred.download_dir  # Новое поле
            }

    def set_settings(self, settings):
        if 'host' not in settings:
            raise ValueError("Host is required")
        
        with db_session() as db:
            cred = db.query(TransmissionCredentials).first()
            if not cred:
                cred = TransmissionCredentials()
                db.add(cred)
            cred.host = settings['host']
            cred.port = settings.get('port', self.DEFAULT_PORT)
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)
            cred.download_dir = settings.get('download_dir', None)  # Новое поле

    def add_torrent(self, torrent, torrent_settings):
        if not torrent:
            raise ValueError("Torrent data is required")
        
        client = self.check_connection()
        if not client:
            return False
        
        with db_session() as db:
            cred = db.query(TransmissionCredentials).first()
            download_dir = cred.download_dir if cred else None
        
        torrent_settings_dict = {}
        if download_dir:
            torrent_settings_dict['download-dir'] = download_dir
        
        try:
            client.add_torrent(base64.b64encode(torrent).decode('utf-8'), **torrent_settings_dict)
            return True
        except transmissionrpc.TransmissionError as e:
            logger.error(f"Error adding torrent: {e}")
            return False
