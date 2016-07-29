from monitorrent.plugins.notifiers.pushbullet import PushbulletNotifierPlugin, PushbulletSettings, PushbulletException
from tests import use_vcr, DbTestCase


class PushbulletHelper:
    fake_token = 'this_is_fake'
    real_token = None

    def __init__(self, token=None):
        self.real_token = token or self.fake_token


class PushbulletTest(DbTestCase):
    def setUp(self):
        super(PushbulletTest, self).setUp()
        self.notifier = PushbulletNotifierPlugin()
        self.helper = PushbulletHelper()

    @use_vcr
    def test_notify_failed(self):
        with self.assertRaises(PushbulletException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token was not specified")

        settings = PushbulletSettings()
        self.notifier.update_settings(settings)

        with self.assertRaises(PushbulletException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 1)
        self.assertEqual(e.exception.message, "Access Token was not specified")

        settings.access_token = self.helper.fake_token
        self.notifier.update_settings(settings)
        with self.assertRaises(PushbulletException) as e:
            self.notifier.notify('hello', 'yaay')
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(e.exception.message, 'Failed to send Pushbullet notification')

    @use_vcr
    def test_notify(self):
        settings = PushbulletSettings()
        settings.access_token = self.helper.real_token
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay')
        self.assertTrue(response)

    @use_vcr
    def test_notify_link(self):
        settings = PushbulletSettings()
        settings.access_token = self.helper.real_token
        self.notifier.update_settings(settings)
        response = self.notifier.notify('hello', 'yay', 'http://mywebsite.com')
        self.assertTrue(response)
