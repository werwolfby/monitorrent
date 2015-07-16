import transmissionrpc
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, DBSession
from plugin_managers import register_plugin


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
                transmissionrpc.Client(address=cred.host, port=cred.port,
                                       user=cred.username, password=cred.password)
                return True
            except transmissionrpc.TransmissionError:
                return False

register_plugin('client', 'transmission', TransmissionClientPlugin())
