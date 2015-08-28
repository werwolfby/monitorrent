from monitorrent.tests import DbTestCase
from monitorrent.settings_manager import SettingsManager


class SettingsManagerTest(DbTestCase):
    def test_get_default_password(self):
        settings_manager = SettingsManager()

        self.assertEqual('monitorrent', settings_manager.get_password())

    def test_set_password(self):
        settings_manager = SettingsManager()

        value = 'p@$$w0rd!'
        settings_manager.set_password(value)

        self.assertEqual(value, settings_manager.get_password())

    def test_get_default_is_authentication_enabled(self):
        settings_manager = SettingsManager()

        self.assertTrue(settings_manager.get_is_authentication_enabled())

    def test_set_is_authentication_enabled(self):
        settings_manager = SettingsManager()

        value = False
        settings_manager.set_is_authentication_enabled(value)

        self.assertEqual(value, settings_manager.get_is_authentication_enabled())

    def test_enable_disable_authentication(self):
        settings_manager = SettingsManager()

        settings_manager.disable_authentication()

        self.assertFalse(settings_manager.get_is_authentication_enabled())

        settings_manager.enable_authentication()

        self.assertTrue(settings_manager.get_is_authentication_enabled())
