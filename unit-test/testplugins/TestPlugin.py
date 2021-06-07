import logging

from Plugin import PluginSPI


class Plugin(PluginSPI):

    def __init__(self, logger=logging.getLogger()):
        super().__init__(logger)
        logger.info('TEST PLUGIN')