from ddt import ddt, data
from monitorrent.tests import DbTestCase
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsManagerTest(DbTestCase):
    def setUp(self):
        super(SettingsManagerTest, self).setUp()
        self.settings_manager = SettingsManager() 

    def test_get_default_password(self):
        self.assertEqual('monitorrent', self.settings_manager.get_password())

    def test_set_password(self):
        value = 'p@$$w0rd!'
        self.settings_manager.set_password(value)

        self.assertEqual(value, self.settings_manager.get_password())

    def test_get_default_is_authentication_enabled(self):
        self.assertTrue(self.settings_manager.get_is_authentication_enabled())

    def test_set_is_authentication_enabled(self):
        value = False
        self.settings_manager.set_is_authentication_enabled(value)

        self.assertEqual(value, self.settings_manager.get_is_authentication_enabled())

    def test_enable_disable_authentication(self):
        self.settings_manager.disable_authentication()

        self.assertFalse(self.settings_manager.get_is_authentication_enabled())

        self.settings_manager.enable_authentication()

        self.assertTrue(self.settings_manager.get_is_authentication_enabled())

    def test_default_client(self):
        self.assertIsNone(self.settings_manager.get_default_client())

        client = 'transmission'
        self.settings_manager.set_default_client(client)

        self.assertEqual(client, self.settings_manager.get_default_client())

    def test_get_is_developer_mode(self):
        self.assertFalse(self.settings_manager.get_is_developer_mode())

    @data(True, False)
    def test_set_is_developer_mode(self, value):
        self.settings_manager.set_is_developer_mode(value)

        self.assertEqual(value, self.settings_manager.get_is_developer_mode())

    def test_get_default_requests_timeout(self):
        self.assertEqual(10, self.settings_manager.requests_timeout)

    def test_set_requests_timeout(self):
        self.assertEqual(10, self.settings_manager.requests_timeout)

        self.settings_manager.requests_timeout = 20

        self.assertEqual(20, self.settings_manager.requests_timeout)

    def test_set_float_requests_timeout(self):
        self.assertEqual(10, self.settings_manager.requests_timeout)

        self.settings_manager.requests_timeout = 20.7

        self.assertEqual(20.7, self.settings_manager.requests_timeout)

    def test_get_default_plugin_settings(self):
        self.assertEqual(10, self.settings_manager.plugin_settings.requests_timeout)

    def test_set_plugin_settings(self):
        plugin_settings = self.settings_manager.plugin_settings
        self.assertEqual(10, plugin_settings.requests_timeout)

        plugin_settings.requests_timeout = 20
        self.settings_manager.plugin_settings = plugin_settings

        self.assertEqual(20, self.settings_manager.plugin_settings.requests_timeout)

    def test_set_float_plugin_settings(self):
        plugin_settings = self.settings_manager.plugin_settings
        self.assertEqual(10, plugin_settings.requests_timeout)

        plugin_settings.requests_timeout = 20.3
        self.settings_manager.plugin_settings = plugin_settings

        self.assertEqual(20.3, self.settings_manager.plugin_settings.requests_timeout)
