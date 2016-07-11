from unittest import TestCase
from mock import Mock, MagicMock

from ddt import ddt

from monitorrent.plugin_managers import NotifierManager


@ddt
class NotifierManagerTest(TestCase):
    NOTIFIER1_NAME = 'notifier1'
    NOTIFIER2_NAME = 'notifier2'

    def setUp(self):
        super(NotifierManagerTest, self).setUp()

        self.notifier1 = Mock()
        self.notifier2 = Mock()

        self.notifier_manager = NotifierManager(
            {self.NOTIFIER1_NAME: self.notifier1, self.NOTIFIER2_NAME: self.notifier2})

    def test_init(self):
        notifier_manager = NotifierManager()
        self.assertIsNotNone(notifier_manager.notifiers)

    def test_get_settings(self):
        settings1 = {'uri': 'uri1', 'login': 'login1', 'password': 'password1'}
        settings2 = {'uri': 'uri2', 'login': 'login2', 'password': 'password2'}

        self.notifier1.get_settings = MagicMock(return_value=settings1)
        self.notifier2.get_settings = MagicMock(return_value=settings2)

        settings = self.notifier_manager.get_settings(self.NOTIFIER1_NAME)
        self.assertEqual(settings1, settings)
        self.notifier1.get_settings.assert_called_with()
        self.notifier2.get_settings.assert_not_called()

        settings = self.notifier_manager.get_settings(self.NOTIFIER2_NAME)
        self.assertEqual(settings2, settings)
        self.notifier2.get_settings.assert_called_with()

    def test_get_notifier(self):
        notifier = self.notifier_manager.get_notifier(self.NOTIFIER1_NAME).get('notifier')
        self.assertEqual(self.notifier1, notifier)

        notifier = self.notifier_manager.get_notifier(self.NOTIFIER2_NAME).get('notifier')
        self.assertEqual(self.notifier2, notifier)

    def test_update_settings(self):
        settings1 = {'uri': 'uri1', 'login': 'login1', 'password': 'password1'}
        settings2 = {'uri': 'uri2', 'login': 'login2', 'password': 'password2'}

        self.notifier1.update_settings = MagicMock()
        self.notifier2.update_settings = MagicMock()

        self.notifier_manager.update_settings(self.NOTIFIER1_NAME, settings1)
        self.notifier1.update_settings.assert_called_with(settings1)
        self.notifier2.update_settings.assert_not_called()

        self.notifier_manager.update_settings(self.NOTIFIER2_NAME, settings2)
        self.notifier2.update_settings.assert_called_with(settings2)

    def test_send_test_message(self):
        notify1 = MagicMock()
        notify2 = MagicMock()

        self.notifier1.notify = notify1
        self.notifier2.notify = notify2

        self.notifier_manager.send_test_message(self.NOTIFIER1_NAME)
        notify1.assert_called_once_with("Test Message", "This is monitorrent test message",
                                        "https://github.com/werwolfby/monitorrent")
        notify2.assert_not_called()

        self.notifier_manager.send_test_message(self.NOTIFIER2_NAME)
        notify2.assert_called_once_with("Test Message", "This is monitorrent test message",
                                        "https://github.com/werwolfby/monitorrent")

    def test_get_enabled_new_settings(self):
        # new should be false
        self.notifier1.get_settings = MagicMock(return_value=None)
        self.assertFalse(self.notifier_manager.get_enabled(self.NOTIFIER1_NAME))

    def test_set_enabled(self):
        self.notifier_manager.set_enabled(self.NOTIFIER1_NAME, True)
        self.assertTrue(self.notifier_manager.get_enabled(self.NOTIFIER1_NAME))
        self.notifier_manager.set_enabled(self.NOTIFIER1_NAME, False)
        self.assertFalse(self.notifier_manager.get_enabled(self.NOTIFIER1_NAME))

    def test_set_enabled_new(self):
        self.notifier1.get_settings = MagicMock(return_value=None)
        self.notifier1.settings_class = MagicMock
        self.notifier_manager.set_enabled(self.NOTIFIER1_NAME, True)
