import importlib
import logging
from configparser import ConfigParser


class PluginLoader:

    def __init__(self, plugin_config, plugin_folder):
        self.logger = logging.getLogger('PluginLoader')
        self.plugins = {}

        self.logger.info("Loading Plugin configuration ...")
        # Load the plugin configuration file
        plugin_info = ConfigParser()
        plugin_info.read(plugin_config)

        self.logger.info("Done loading Plugin configuration")

        # Load plugins
        self.logger.info("Loading Plugins ...")

        for plugin_id, plugin_path in plugin_info['Electric Meter Plugins'].items():
            self.logger.info("Loading %s", str(plugin_id))
            plugin_logger = logging.getLogger(self.logger.name + '.' + str(plugin_id))
            self.plugins[plugin_id] = importlib.import_module('.' + plugin_path, plugin_folder).Plugin(plugin_logger)
            self.logger.info("Loaded %s", str(plugin_id))

        self.logger.info("Plugins loaded")

    def get_plugin(self, plugin_id):
        return self.plugins[plugin_id]

