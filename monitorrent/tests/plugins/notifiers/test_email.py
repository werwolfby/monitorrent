import smtplib

from mock import Mock, ANY

from monitorrent.plugins.notifiers.email_sender import EmailNotifierPlugin, EmailException, EmailSettings, EmailSecurity
from monitorrent.tests import DbTestCase


class EmailHelper:
    fake_host = u'this_is_fake'
    fake_port = 443
    fake_login = None
    fake_password = None
    fake_to_addr = u'this_is_fake@fake.com'
    fake_connection_security = False

    real_host = None
    real_port = None
    real_login = None
    real_password = None
    real_to_addr = None
    real_connection_security = None

    def __init__(self, host=None, port=None, login=None, password=None, to_addr=None, connection_security=None):
        self.real_host = host or self.fake_host
        self.real_port = port or self.fake_port
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_to_addr = to_addr or self.fake_to_addr
        self.real_connection_security = connection_security or self.fake_connection_security


class EmailTest(DbTestCase):
    def setUp(self):
        super(EmailTest, self).setUp()
        self.notifier = EmailNotifierPlugin()
        self.helper = EmailHelper()
        self.helper.real_host = "localhost"
        self.helper.real_port = "1025"
        self.helper.real_connection_security = 'SSL'
        self.helper.real_login = "reallogin"
        self.helper.real_password = "realpassword"

    def test_notify_failed(self):
        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Settings not specified")

        settings = EmailSettings()
        self.notifier.update_settings(settings)

        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, "SMTP host not specified")

        settings.host = self.helper.real_host
        self.notifier.update_settings(settings)
        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 3)
        self.assertEqual(e.exception.message, "Email to address not specified")

    def test_notify_failed(self):
        settings = EmailSettings()

        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yay')
        self.assertEqual(1, e.exception.code)
        self.assertEqual('Settings not specified', e.exception.message)

        self.notifier.update_settings(settings)
        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yay')
        self.assertEqual(2, e.exception.code)
        self.assertEqual('SMTP host not specified', e.exception.message)

        settings.host = self.helper.real_host
        self.notifier.update_settings(settings)
        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yay')
        self.assertEqual(3, e.exception.code)
        self.assertEqual('Email to address not specified', e.exception.message)

        settings.host = self.helper.real_host
        settings.port = self.helper.real_port
        settings.to_addr = self.helper.real_to_addr
        settings.login = self.helper.real_login
        settings.password = self.helper.real_password
        settings.connection_security = str(self.helper.real_connection_security)
        self.notifier.update_settings(settings)

        server = Mock()
        self.notifier._create_server = Mock(return_value=server)
        self.notifier._server_authenticate = Mock(return_value=server)
        server.sendmail = Mock(side_effect=smtplib.SMTPResponseException(3, "132"))
        with self.assertRaises(EmailException) as e:
            self.notifier.notify('hello', 'yay')
        self.assertEqual(5, e.exception.code)
        self.assertEqual('SMTP: failed to deliver the message', e.exception.message)

    def test_notify(self):
        settings = EmailSettings()

        settings.host = self.helper.real_host
        settings.port = self.helper.real_port
        settings.to_addr = self.helper.real_to_addr
        settings.login = self.helper.real_login
        settings.password = self.helper.real_password
        settings.connection_security = self.helper.real_connection_security
        self.notifier.update_settings(settings)
        server = Mock()
        self.notifier._create_server = Mock(return_value=server)
        self.notifier._server_authenticate = Mock(return_value=server)

        server.sendmail = Mock()
        server.quit = Mock()
        response = self.notifier.notify('hello', 'yay')

        server.sendmail.assert_called_once_with(self.helper.real_login, self.helper.real_to_addr, ANY)
        self.assertTrue(response)
        server.quit.assert_called_once_with()

    def test_notify_link(self):
        settings = EmailSettings()

        settings.host = self.helper.real_host
        settings.port = self.helper.real_port
        settings.to_addr = self.helper.real_to_addr
        settings.login = self.helper.real_login
        settings.password = self.helper.real_password
        settings.connection_security = self.helper.real_connection_security
        self.notifier.update_settings(settings)
        server = Mock()
        self.notifier._create_server = Mock(return_value=server)
        self.notifier._server_authenticate = Mock(return_value=server)

        server.sendmail = Mock()
        server.quit = Mock()
        response = self.notifier.notify('hello', 'yay', 'test_url')

        server.sendmail.assert_called_once_with(self.helper.real_login, self.helper.real_to_addr, ANY)
        self.assertTrue(response)
        server.quit.assert_called_once_with()

    def test_create_server(self):
        settings = EmailSettings()
        settings.host = "smtp.gmail.com"
        settings.to_addr = self.helper.fake_to_addr
        settings.port = 465
        settings.login = self.helper.fake_login
        settings.password = self.helper.fake_password
        settings.timeout = 21
        settings.connection_security = 'SSL'
        self.notifier.update_settings(settings)
        server = EmailNotifierPlugin._create_server(settings)
        self.assertIsInstance(server, smtplib.SMTP_SSL)
        self.assertEqual(server.timeout, 21)

        settings.timeout = None
        settings.port = 587
        settings.connection_security = 'TLS'
        self.notifier.update_settings(settings)
        server = EmailNotifierPlugin._create_server(settings)
        self.assertIsInstance(server, smtplib.SMTP)
        self.assertEqual(server.timeout, 30)

    def test_server_authenticate(self):
        server = Mock()
        settings = EmailSettings()
        server.login = Mock()
        self.notifier._server_authenticate(server, settings)
        server.login.assert_not_called()

        settings.login = self.helper.real_login
        self.notifier._server_authenticate(server, settings)
        server.login.assert_not_called()

        settings.password = self.helper.real_password
        server2 = self.notifier._server_authenticate(server, settings)
        self.assertEqual(server, server2)
        server.login.assert_called_once_with(self.helper.real_login, self.helper.real_password)

        server.quit = Mock()
        server.login = Mock(side_effect=smtplib.SMTPAuthenticationError(3, "123"))
        with self.assertRaises(EmailException) as e:
            self.notifier._server_authenticate(server, settings)
        self.assertEqual(e.exception.code, 4)
        self.assertEqual(e.exception.message, "SMTP login: Invalid login or password")
        server.quit.assert_called_once_with()
