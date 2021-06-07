import unittest

from PluginLoader import PluginLoader
from testplugins.TestPlugin import Plugin


class PluginLoaderTest(unittest.TestCase):

    def setUp(self) -> None:
        # Created plugin config
        with open('plugin-config.ini', 'w') as plugin_config:
            plugin_config.write('[Electric Meter Plugins]\n')
            plugin_config.write('plugin1=TestPlugin')

    def test_plugin_loading(self):
        plugin_loader = PluginLoader('plugin-config.ini', 'testplugins')

        self.assertNotEqual(0, len(plugin_loader.plugins.items()))
        self.assertIn('plugin1', plugin_loader.plugins.keys())
        self.assertEqual(type(plugin_loader.plugins['plugin1']), type(Plugin()))

    # TODO more tests


if __name__ == '__main__':
    unittest.main()
