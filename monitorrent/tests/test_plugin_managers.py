import os
from mock import Mock, MagicMock, patch
from monitorrent.tests import TestCase
from monitorrent.plugin_managers import load_plugins, register_plugin, get_plugins, get_all_plugins


class LoadPluginsTest(TestCase):
    def test_load_plugins(self):
        dir_name = os.path.dirname(os.path.realpath(os.path.join(__file__, '..')))
        walk_result = [
            (dir_name, ['plugins'], ['__init__.py']),
            (os.path.join(dir_name, 'plugins'), [], ['__init__.py', 'plugin1.py', 'plugin2.py']),
        ]
        os_walk_mock = MagicMock(return_value=walk_result)
        import_mock = MagicMock()
        with patch('monitorrent.plugin_managers.os.walk', os_walk_mock), \
                patch('monitorrent.plugin_managers.__import__', import_mock, create=True):
            load_plugins('plugins')

        self.assertTrue(os_walk_mock.call_count, 1)
        self.assertTrue(import_mock.call_count, 2)
        import_mock.assert_any_call('monitorrent.plugins.plugin1')
        import_mock.assert_any_call('monitorrent.plugins.plugin2')


class RegisterPluginTest(TestCase):
    def test_register(self):
        plugin1 = object()
        plugin2 = object()
        plugin3 = object()
        upgrade = lambda *args, **kwargs: None

        with patch('monitorrent.plugin_managers.plugins', dict()), \
                patch('monitorrent.plugin_managers.upgrades', dict()) as upgrades:
            register_plugin('type1', 'name1', plugin1)
            register_plugin('type1', 'name2', plugin2)
            register_plugin('type2', 'name3', plugin3, upgrade=upgrade)

            self.assertEqual(get_all_plugins(), {'name1': plugin1, 'name2': plugin2, 'name3': plugin3})
            self.assertEqual(get_plugins('type1'), {'name1': plugin1, 'name2': plugin2})
            self.assertEqual(get_plugins('type2'), {'name3': plugin3})

            self.assertEqual(upgrades, {'name3': upgrade})
