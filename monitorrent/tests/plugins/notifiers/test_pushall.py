# coding=utf-8
from monitorrent.plugins.notifiers.pushall import PushAllNotifierPlugin, PushAllSettings, PushAllException
from monitorrent.tests import use_vcr, DbTestCase


class PushAllTest(DbTestCase):
    def setUp(self):
        super(PushAllTest, self).setUp()
        self.notifier = PushAllNotifierPlugin()
        self.fake_id = 1234
        self.fake_token = 'this_is_fake'
        self.read_id = self.fake_id
        self.real_token = self.fake_token

    @use_vcr
    def test_notify_failed(self):
        with self.assertRaises(PushAllException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings = PushAllSettings()
        self.notifier.update_settings(settings)

        with self.assertRaises(PushAllException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = self.fake_token
        self.notifier.update_settings(settings)
        with self.assertRaises(PushAllException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = None
        settings.user_id = self.fake_id
        self.notifier.update_settings(settings)
        with self.assertRaises(PushAllException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token or User Id was not specified")

        settings.access_token = self.fake_token
        settings.user_id = self.fake_id
        self.notifier.update_settings(settings)
        with self.assertRaises(PushAllException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to send PushAll notification')

    @use_vcr
    def test_notify(self):
        settings = PushAllSettings()
        settings.access_token = self.real_token
        settings.user_id = self.read_id
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay')
        self.assertTrue(response)

    @use_vcr
    def test_notify_link(self):
        settings = PushAllSettings()
        settings.access_token = self.real_token
        settings.user_id = self.read_id
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay', 'http://mywebsite.com')
        self.assertTrue(response)


