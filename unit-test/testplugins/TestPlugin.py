import logging

from Plugin import ElectricMeterPluginSPI


class Plugin(ElectricMeterPluginSPI):

    def create_electric_meter(self, name, custom):
        pass

    def json_serialize_electric_meter(self, electric_meter):
        pass

    def json_load_electric_meter(self, serialized_json):
        pass

    def change_electric_meter(self, electric_meter, name, custom):
        pass

    def validate_custom_data(self, custom):
        pass

    def __init__(self, logger=logging.getLogger()):
        super().__init__(logger)
        logger.info('TEST PLUGIN')
