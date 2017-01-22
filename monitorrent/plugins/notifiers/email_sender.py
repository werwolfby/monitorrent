# coding=utf-8
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Enum
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier, NotifierType
import enum

PLUGIN_NAME = 'email'


class EmailException(NotificationException):
    pass


class EmailSecurity(enum.Enum):
    Empty = 1
    SSL = 2
    TLS = 3


class EmailSettings(Notifier):
    __tablename__ = "email_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)
    host = Column(String)
    port = Column(Integer)
    login = Column(String)
    password = Column(String)
    to_addr = Column(String)
    timeout = Column(Integer)
    connection_security = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class EmailNotifierPlugin(NotifierPlugin):
    settings_fields = ['host', 'port', 'login', 'password', 'to_addr', 'timeout', 'connection_security']

    @property
    def get_type(self):
        return NotifierType.full_text

    __from_addr = "noreply@monitorrent.com"
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
            'label': 'Login/From Email',
            'model': 'login',
            'flex': 50
        }, {
            'type': 'password',
            'label': 'Password',
            'model': 'password',
            'flex': 50
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'To Address',
            'model': 'to_addr',
            'flex': 60
        }, {
            'type': 'text',
            'label': 'Timeout',
            'model': 'timeout',
            'flex': 40
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'select',
            'options': ["None", "SSL", "TLS"],
            'label': 'Connection Security',
            'model': 'connection_security',
            'flex': 40
        }]
    }]

    @property
    def settings_class(self):
        return EmailSettings

    @staticmethod
    def _create_server(settings):
        if settings.connection_security == 'SSL':
            server = smtplib.SMTP_SSL(settings.host, settings.port)
        else:
            server = smtplib.SMTP(settings.host, settings.port)
        server.timeout = settings.timeout or 30
        if settings.connection_security == 'TLS':
            server.starttls()
        return server

    @staticmethod
    def _server_authenticate(server, settings):
        if settings.login and settings.password:
            try:
                server.login(settings.login, settings.password)
            except smtplib.SMTPAuthenticationError as e:
                server.quit()
                raise EmailException(4, 'SMTP login: Invalid login or password')
        return server

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings:
            raise EmailException(1, 'Settings not specified')
        if not settings.host:
            raise EmailException(2, 'SMTP host not specified')
        if not settings.to_addr:
            raise EmailException(3, 'Email to address not specified')
        server = self._create_server(settings)
        self._server_authenticate(server, settings)
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.login
            msg['To'] = settings.to_addr
            msg['Subject'] = header
            msg.attach(MIMEText(body))
            if url:
                msg.attach(MIMEText('\n' + url))

            server.sendmail(settings.login, settings.to_addr, msg.as_string())
            return True
        except smtplib.SMTPResponseException as e:
            raise EmailException(5, 'SMTP: failed to deliver the message')
        finally:
            server.quit()

register_plugin('notifier', 'email', EmailNotifierPlugin())
