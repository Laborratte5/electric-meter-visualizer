

class ElectricMeterPluginSPI:

    def __init__(self, logger):
        logger.info('Initializing plugin')

    def validate_custom_data(self, custom):
        raise NotImplementedError

    def create_electric_meter(self, name, custom):
        raise NotImplementedError

    def json_serialize_electric_meter(self, electric_meter):
        raise NotImplementedError

    def json_load_electric_meter(self, serialized_json):
        raise NotImplementedError

    def change_electric_meter(self, electric_meter, name, custom):
        raise NotImplementedError
