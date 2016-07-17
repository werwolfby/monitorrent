from unittest import TestCase
from mock import Mock, MagicMock, PropertyMock

from ddt import ddt

from monitorrent.db import DBSession
from monitorrent.plugin_managers import NotifierManager
from monitorrent.plugins.notifiers import Notifier, NotifierType
from monitorrent.tests import DbTestCase

NOTIFIER1_NAME = 'notifier1'
NOTIFIER2_NAME = 'notifier2'


@ddt
class NotifierManagerTest(TestCase):
    def setUp(self):
        super(NotifierManagerTest, self).setUp()

        self.notifier1 = Mock()
        self.notifier2 = Mock()

        self.notifier_manager = NotifierManager(
            {NOTIFIER1_NAME: self.notifier1, NOTIFIER2_NAME: self.notifier2})

    def test_init(self):
        notifier_manager = NotifierManager()
        self.assertIsNotNone(notifier_manager.notifiers)

    def test_get_settings(self):
        settings1 = {'uri': 'uri1', 'login': 'login1', 'password': 'password1'}
        settings2 = {'uri': 'uri2', 'login': 'login2', 'password': 'password2'}

        self.notifier1.get_settings = MagicMock(return_value=settings1)
        self.notifier2.get_settings = MagicMock(return_value=settings2)

        settings = self.notifier_manager.get_settings(NOTIFIER1_NAME)
        self.assertEqual(settings1, settings)
        self.notifier1.get_settings.assert_called_with()
        self.notifier2.get_settings.assert_not_called()

        settings = self.notifier_manager.get_settings(NOTIFIER2_NAME)
        self.assertEqual(settings2, settings)
        self.notifier2.get_settings.assert_called_with()

    def test_get_notifier(self):
        notifier = self.notifier_manager.get_notifier(NOTIFIER1_NAME).get('notifier')
        self.assertEqual(self.notifier1, notifier)

        notifier = self.notifier_manager.get_notifier(NOTIFIER2_NAME).get('notifier')
        self.assertEqual(self.notifier2, notifier)

    def test_update_settings(self):
        settings1 = {'uri': 'uri1', 'login': 'login1', 'password': 'password1'}
        settings2 = {'uri': 'uri2', 'login': 'login2', 'password': 'password2'}

        self.notifier1.update_settings = MagicMock()
        self.notifier2.update_settings = MagicMock()

        self.notifier_manager.update_settings(NOTIFIER1_NAME, settings1)
        self.notifier1.update_settings.assert_called_with(settings1)
        self.notifier2.update_settings.assert_not_called()

        self.notifier_manager.update_settings(NOTIFIER2_NAME, settings2)
        self.notifier2.update_settings.assert_called_with(settings2)

    def test_send_test_message(self):
        notify1 = MagicMock()
        notify2 = MagicMock()

        self.notifier1.notify = notify1
        self.notifier2.notify = notify2

        self.notifier_manager.send_test_message(NOTIFIER1_NAME)
        notify1.assert_called_once_with("Test Message", "This is monitorrent test message",
                                        "https://github.com/werwolfby/monitorrent")
        notify2.assert_not_called()

        self.notifier_manager.send_test_message(NOTIFIER2_NAME)
        notify2.assert_called_once_with("Test Message", "This is monitorrent test message",
                                        "https://github.com/werwolfby/monitorrent")

    def test_get_enabled_new_settings(self):
        # new should be false
        self.notifier1.get_settings = MagicMock(return_value=None)
        self.assertFalse(self.notifier_manager.get_enabled(NOTIFIER1_NAME))

    def test_set_enabled(self):
        self.notifier_manager.set_enabled(NOTIFIER1_NAME, True)
        self.assertTrue(self.notifier_manager.get_enabled(NOTIFIER1_NAME))
        self.notifier_manager.set_enabled(NOTIFIER1_NAME, False)
        self.assertFalse(self.notifier_manager.get_enabled(NOTIFIER1_NAME))

    def test_set_enabled_new(self):
        self.notifier1.get_settings = MagicMock(return_value=None)
        self.notifier1.settings_class = MagicMock
        self.notifier_manager.set_enabled(NOTIFIER1_NAME, True)


class TestNotifier1Settings(Notifier):
    __mapper_args__ = {
        'polymorphic_identity': NOTIFIER1_NAME
    }


class TestNotifier2Settings(Notifier):
    __mapper_args__ = {
        'polymorphic_identity': NOTIFIER2_NAME
    }


class NotifierManagerNotificationsTest(DbTestCase):
    def setUp(self):
        super(NotifierManagerNotificationsTest, self).setUp()
        self.settings1 = TestNotifier1Settings()
        self.settings1.type = NOTIFIER1_NAME
        self.settings1.is_enabled = True
        self.settings2 = TestNotifier2Settings()
        self.settings2.is_enabled = False
        self.settings2.type = NOTIFIER2_NAME

        with DBSession() as db:
            db.add(self.settings1)
            db.add(self.settings2)

        self.notifier1 = MagicMock()
        self.notifier2 = MagicMock()

        self.notifier_manager = NotifierManager(
            {NOTIFIER1_NAME: self.notifier1, NOTIFIER2_NAME: self.notifier2})

    def test_get_enabled_notifiers(self):
        enabled = list(self.notifier_manager.get_enabled_notifiers())
        self.assertEqual(1, len(enabled))
        self.assertEqual(self.notifier1, enabled[0])

    def test_begin_execute(self):
        message = ""
        message = self.notifier_manager.begin_execute(message)
        self.assertEqual("", message)

    def test_topic_status_updated(self):
        p = PropertyMock(return_value=NotifierType.short_text)
        type(self.notifier1).get_type = p
        self.notifier1.notify = MagicMock()
        message = "TestMessage"
        ongoing_message = ""

        ongoing_message = self.notifier_manager.topic_status_updated(ongoing_message, message)
        self.notifier1.notify.assert_called_once_with("Monitorrent Update", message)
        self.assertEqual("\nTestMessage", ongoing_message)

    def test_end_execute_not_called(self):
        ongoing_message = ""
        p = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier1).get_type = p
        self.notifier1.notify = MagicMock()

        self.notifier_manager.end_execute(ongoing_message)

        self.assertEqual("", ongoing_message)
        self.notifier1.notify.assert_not_called()

    def test_end_execute_called(self):
        ongoing_message = "Some message"
        p = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier1).get_type = p
        self.notifier1.notify = MagicMock()

        self.notifier_manager.end_execute(ongoing_message)

        self.notifier1.notify.assert_called_with("Monitorrent Update", "Monitorrent execute result + \nSome message")
