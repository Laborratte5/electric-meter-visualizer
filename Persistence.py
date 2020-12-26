import json

STATE_FILE = 'state.json'


class State:

    @classmethod
    def get_state(cls):
        pass

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self, f, cls=StateJsonEncoder)

    def __init__(self):
        # Initialize with default values
        self.next_id = 10
        self.electric_meters = {}

    def get_next_id(self):
        return self.next_id

    def set_next_id(self, next_id):
        self.next_id = next_id
        self.save_state()

    def get_electric_meters(self):
        return self.electric_meters

    def set_electric_meters(self, electric_meters):
        self.electric_meters = electric_meters
        self.save_state()


class StateJsonEncoder(json.JSONEncoder):
    def encode_state(self, state):
        return {
            'next_id': state.get_next_id(),
            'electric_meters': [self.encode_electric_meter(meter_id, meter)
                                for meter_id, meter in state.electric_meters.items()]
        }

    def encode_electric_meter(self, meter_id, electric_meter):
        meter_dict = {
            'id': meter_id,
            'name': electric_meter.name,
            'value': electric_meter.value,
            'pin': electric_meter.pin,
            'active_low': electric_meter.active_low,
            'count': electric_meter.count
        }

    def default(self, o):
        if isinstance(o, State):
            # State to dict
            return self.encode_state(o)
        else:
            return json.JSONEncoder.default(self, o)


class StateJsonDecoder:
    # TODO
    pass


class InvalidStateFileException(Exception):
    pass
