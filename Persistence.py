import json
import os
from json.decoder import JSONDecodeError

from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup

STATE_FILE = 'state.json'


class State:

    @classmethod
    def get_state(cls):
        if os.path.isfile(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                decoder = StateJsonDecoder()
                try:
                    state = json.load(f, object_hook=decoder.decode)
                except JSONDecodeError as jsonError:
                    raise InvalidStateFileException from jsonError
                return state
        return State()

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
        # Add flag if this meter is a Mockup, so at deserialization the correct type can be instantiated
        if isinstance(electric_meter, ElectricMeterMockup):
            meter_dict['_mockup_'] = True

        return meter_dict

    def default(self, o):
        if isinstance(o, State):
            # State to dict
            return self.encode_state(o)
        else:
            return json.JSONEncoder.default(self, o)


class StateJsonDecoder:

    def is_state(self, o):
        return all(key in ('next_id', 'electric_meters') for key in o.keys())

    def is_electric_meter(self, o):
        return all(key in o.keys() for key in ('id', 'name', 'value', 'pin', 'active_low', 'count'))

    def decode_state(self, o):
        state = State()
        state.next_id = o['next_id']
        state.electric_meters = {meter_id: meter for meter_id, meter in o['electric_meters']}
        return state

    def decode_electric_meter(self, o):
        meter_id = o['id']
        value = o['value']
        count = o['count']
        name = o['name']
        pin = o['pin']
        active_low = o['active_low']

        if '_mockup_' in o.keys():
            electric_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            electric_meter = ElectricMeter(value, pin, active_low, name)
        electric_meter.count = count

        return meter_id, electric_meter

    def decode(self, o):
        if self.is_state(o):
            # deserialize state
            return self.decode_state(o)
        elif self.is_electric_meter(o):
            # deserialize electric meter
            return self.decode_electric_meter(o)
        else:
            raise ValueError('Error decoding state file')


class InvalidStateFileException(Exception):
    pass
