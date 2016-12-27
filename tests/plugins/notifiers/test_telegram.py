from monitorrent.plugins.notifiers import NotifierType
from monitorrent.plugins.notifiers.telegram import TelegramNotifierPlugin, TelegramSettings, TelegramException
from tests import use_vcr, DbTestCase


class TelegramHelper:
    fake_token = 'this_is_fake'
    fake_chat_id = '12343'

    real_token = None
    real_chat_id = None

    def __init__(self, token=None, chat_id=None):
        self.real_token = token or self.fake_token
        self.real_chat_id = chat_id or self.fake_chat_id


class TelegramTest(DbTestCase):
    def setUp(self):
        super(TelegramTest, self).setUp()
        self.notifier = TelegramNotifierPlugin()
        self.helper = TelegramHelper()

    def test_get_notifier_type(self):
        self.assertEqual(NotifierType.short_text, self.notifier.get_type)

    @use_vcr
    def test_notify_failed(self):
        with self.assertRaises(TelegramException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings = TelegramSettings()
        self.notifier.update_settings(settings)

        with self.assertRaises(TelegramException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = self.helper.fake_token
        self.notifier.update_settings(settings)
        with self.assertRaises(TelegramException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = None
        settings.chat_id = self.helper.fake_chat_id
        self.notifier.update_settings(settings)
        with self.assertRaises(TelegramException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = self.helper.fake_token
        settings.chat_id = self.helper.fake_chat_id
        self.notifier.update_settings(settings)
        with self.assertRaises(TelegramException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to send Telegram notification')

    @use_vcr
    def test_notify(self):
        settings = TelegramSettings()
        settings.access_token = self.helper.real_token
        settings.chat_id = self.helper.real_chat_id
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay')
        self.assertTrue(response)

    @use_vcr
    def test_notify_link(self):
        settings = TelegramSettings()
        settings.access_token = self.helper.real_token
        settings.chat_id = self.helper.real_chat_id
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay', 'http://mywebsite.com')
        self.assertTrue(response)
