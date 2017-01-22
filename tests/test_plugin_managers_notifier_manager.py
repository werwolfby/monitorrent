from unittest import TestCase
from mock import Mock, MagicMock, PropertyMock, call

from ddt import ddt

from monitorrent.db import DBSession
from monitorrent.plugin_managers import NotifierManager
from monitorrent.plugins.notifiers import Notifier, NotifierType
from tests import DbTestCase

NOTIFIER1_NAME = 'notifier1'
NOTIFIER2_NAME = 'notifier2'
NOTIFIER3_NAME = 'notifier3'


@ddt
class NotifierManagerTest(TestCase):
    def setUp(self):
        super(NotifierManagerTest, self).setUp()

        self.settings_manager = Mock()

        self.notifier1 = Mock()
        self.notifier2 = Mock()

        # noinspection PyTypeChecker
        self.notifier_manager = NotifierManager(self.settings_manager,
            {NOTIFIER1_NAME: self.notifier1, NOTIFIER2_NAME: self.notifier2})

    def test_init(self):
        # noinspection PyTypeChecker
        notifier_manager = NotifierManager(self.settings_manager)
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


class Notifier1Settings(Notifier):
    __mapper_args__ = {
        'polymorphic_identity': NOTIFIER1_NAME
    }


class Notifier2Settings(Notifier):
    __mapper_args__ = {
        'polymorphic_identity': NOTIFIER2_NAME
    }


class Notifier3Settings(Notifier):
    __mapper_args__ = {
        'polymorphic_identity': NOTIFIER3_NAME
    }


class NotifierManagerNotificationsTest(DbTestCase):
    def setUp(self):
        super(NotifierManagerNotificationsTest, self).setUp()

        levels = ['DOWNLOAD', 'ERROR', 'STATUS_CHANGED']
        self.settings_manager = Mock()
        self.settings_manager.get_external_notifications_levels = Mock(return_value=levels)

        self.settings1 = Notifier1Settings()
        self.settings1.is_enabled = True
        self.settings1.type = NOTIFIER1_NAME

        self.settings2 = Notifier2Settings()
        self.settings2.is_enabled = False
        self.settings2.type = NOTIFIER2_NAME

        self.settings3 = Notifier3Settings()
        self.settings3.is_enabled = True
        self.settings3.type = NOTIFIER3_NAME

        with DBSession() as db:
            db.add(self.settings1)
            db.add(self.settings2)
            db.add(self.settings3)

        self.notifier1 = MagicMock()
        self.notifier1.get_type = NotifierType.short_text

        self.notifier2 = MagicMock()
        self.notifier2.get_type = NotifierType.short_text

        self.notifier3 = MagicMock()
        self.notifier3.get_type = NotifierType.full_text

        # noinspection PyTypeChecker
        self.notifier_manager = NotifierManager(
            self.settings_manager,
            {
                NOTIFIER1_NAME: self.notifier1,
                NOTIFIER2_NAME: self.notifier2,
                NOTIFIER3_NAME: self.notifier3
            })

    def test_get_enabled_notifiers(self):
        enabled = list(self.notifier_manager.get_enabled_notifiers())
        self.assertEqual(2, len(enabled))
        self.assertEqual(self.notifier1, enabled[0])
        self.assertEqual(self.notifier3, enabled[1])

    def test_short_text_notify_failed(self):
        self.notifier1.notify = Mock(side_effect=Exception)
        message = "TestMessage"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify(message)

        self.notifier1.notify.assert_called_once_with("Monitorrent Update", message)
        self.notifier2.notify.assert_not_called()
        # should be replaced by contains message instead of full string compare
        self.notifier3.notify.assert_called_once_with("Monitorrent Update", "Monitorrent execute result\n" + message)

    def test_full_text_notify_failed(self):
        self.notifier3.notify = Mock(side_effect=Exception)
        message = "TestMessage"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify(message)

        self.notifier1.notify.assert_called_once_with("Monitorrent Update", message)
        self.notifier2.notify.assert_not_called()
        # should be replaced by contains message instead of full string compare
        self.notifier3.notify.assert_called_once_with("Monitorrent Update", "Monitorrent execute result\n" + message)

    def test_end_execute_not_called(self):
        with self.notifier_manager.execute():
            pass

        self.notifier1.notify.assert_not_called()
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_not_called()

    def test_end_execute_called(self):
        message = "Some message"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify(message)

        self.notifier1.notify.assert_called_once_with("Monitorrent Update", message)
        self.notifier2.notify.assert_not_called()
        # should be replaced by contains message instead of full string compare
        self.notifier3.notify.assert_called_once_with("Monitorrent Update", "Monitorrent execute result\n" + message)

    def test_notify_few_times(self):
        p1 = PropertyMock(return_value=NotifierType.short_text)
        type(self.notifier1).get_type = p1

        p2 = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier2).get_type = p2

        message1 = "Test message 1"
        message2 = "Test message 2"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify(message1)
            notifier_execute.notify(message2)

        self.notifier1.notify.assert_has_calls([call("Monitorrent Update", message1),
                                                call("Monitorrent Update", message2)])
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_called_once_with("Monitorrent Update",
                                                      "Monitorrent execute result\n" +
                                                      message1 + "\n" +
                                                      message2)

    def test_disabled_notify_failed(self):
        p1 = PropertyMock(return_value=NotifierType.short_text)
        type(self.notifier1).get_type = p1

        p2 = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier2).get_type = p2

        message1 = "Test message 1"
        message2 = "Test message 2"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_failed(message1)
            notifier_execute.notify_failed(message2)

        self.notifier1.notify.assert_has_calls([call("Monitorrent Update", message1),
                                                call("Monitorrent Update", message2)])
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_called_once_with("Monitorrent Update",
                                                      "Monitorrent execute result\n" +
                                                      message1 + "\n" +
                                                      message2)

        levels = ['DOWNLOAD', 'STATUS_CHANGED']
        self.settings_manager.get_external_notifications_levels = Mock(return_value=levels)

        self.notifier1.notify.reset_mock()
        self.notifier2.notify.reset_mock()
        self.notifier3.notify.reset_mock()

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_failed(message1)
            notifier_execute.notify_failed(message2)

        self.notifier1.notify.assert_not_called()
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_not_called()

    def test_disabled_notify_download(self):
        p1 = PropertyMock(return_value=NotifierType.short_text)
        type(self.notifier1).get_type = p1

        p2 = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier2).get_type = p2

        message1 = "Test message 1"
        message2 = "Test message 2"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_download(message1)
            notifier_execute.notify_download(message2)

        self.notifier1.notify.assert_has_calls([call("Monitorrent Update", message1),
                                                call("Monitorrent Update", message2)])
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_called_once_with("Monitorrent Update",
                                                      "Monitorrent execute result\n" +
                                                      message1 + "\n" +
                                                      message2)

        levels = ['ERROR', 'STATUS_CHANGED']
        self.settings_manager.get_external_notifications_levels = Mock(return_value=levels)

        self.notifier1.notify.reset_mock()
        self.notifier2.notify.reset_mock()
        self.notifier3.notify.reset_mock()

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_download(message1)
            notifier_execute.notify_download(message2)

        self.notifier1.notify.assert_not_called()
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_not_called()

    def test_disabled_notify_status_changed(self):
        p1 = PropertyMock(return_value=NotifierType.short_text)
        type(self.notifier1).get_type = p1

        p2 = PropertyMock(return_value=NotifierType.full_text)
        type(self.notifier2).get_type = p2

        message1 = "Test message 1"
        message2 = "Test message 2"

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_status_changed(message1)
            notifier_execute.notify_status_changed(message2)

        self.notifier1.notify.assert_has_calls([call("Monitorrent Update", message1),
                                                call("Monitorrent Update", message2)])
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_called_once_with("Monitorrent Update",
                                                      "Monitorrent execute result\n" +
                                                      message1 + "\n" +
                                                      message2)

        levels = ['DOWNLOAD', 'ERROR']
        self.settings_manager.get_external_notifications_levels = Mock(return_value=levels)

        self.notifier1.notify.reset_mock()
        self.notifier2.notify.reset_mock()
        self.notifier3.notify.reset_mock()

        with self.notifier_manager.execute() as notifier_execute:
            notifier_execute.notify_status_changed(message1)
            notifier_execute.notify_status_changed(message2)

        self.notifier1.notify.assert_not_called()
        self.notifier2.notify.assert_not_called()
        self.notifier3.notify.assert_not_called()
