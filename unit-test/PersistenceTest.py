import unittest
import os
import random
import json

import Persistence
from ElectricMeterMockup import ElectricMeterMockup
from Persistence import State

def cleanup() -> None:
    if os.path.exists(Persistence.STATE_FILE):
        os.remove(Persistence.STATE_FILE)


def create_state_file(next_id, meter_id, value, pin, active_low, name, count):
    json_data = \
        '''{{"next_id": {next_id}, 
            "electric_meters":[
                {{"id": {id},
                 "value": {value},
                 "count": {count},
                 "name": "{name}",
                 "pin": {pin},
                 "active_low": {active_low}
                }}
            ]
           }}'''.format(next_id=next_id, id=meter_id, value=value, count=count,
                        name=name, pin=pin, active_low=str(active_low).lower())

    with open(Persistence.STATE_FILE, 'w') as state_file:
        state_file.writelines(json_data)


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.isfile(Persistence.STATE_FILE):
            os.remove(Persistence.STATE_FILE)

        self.addCleanup(cleanup)

    def test_get_state(self):
        state = State.get_state()
        self.assertIsNotNone(state)

    def test_save_next_id(self):
        # Setup
        next_id = random.randint(0, 100)
        state = State.get_state()

        # Test
        state.set_next_id(next_id)

        # Assert
        with open(Persistence.STATE_FILE) as state_file:
            obj = json.loads(state_file)
            self.assertEqual(obj['next-id'], str(next_id))

    def test_load_next_id(self):
        # Setup
        next_id = 10
        meter_id = 0
        value = 0
        pin = 0
        active_low = False
        name = 'meter_1'
        count = 0

        create_state_file(next_id, meter_id, value, pin, active_low, name, count)

        # Test
        state = State.get_state()

        # Assert
        self.assertEqual(next_id, state.get_next_id())

    def test_save_electric_meter(self):
        # Setup
        value = 321
        pin = 123
        active_low = False
        name = 'test'
        count = 456
        electric_meter = ElectricMeterMockup(value, pin, active_low, name)
        electric_meter.count = count
        electric_meters = {0: electric_meter}
        state = State.get_state()

        # Test
        state.set_electric_meters(electric_meters)

        # Assertion
        with open(Persistence.STATE_FILE) as state_file:
            obj = json.loads(state_file)
            self.assertEqual(obj['electric-meters'][0]['value'], str(value))
            self.assertEqual(obj['electric-meters'][0]['pin'], str(pin))
            self.assertEqual(obj['electric-meters'][0]['active-low'], str(active_low))
            self.assertEqual(obj['electric-meters'][0]['name'], name)
            self.assertEqual(obj['electric_meters'][0]['count'], str(count))

    def test_load_electric_meter(self):
        # Setup
        meter_id = 1
        value = 321
        pin = 123
        active_low = False
        name = 'test'
        count = 456

        create_state_file(meter_id+1, meter_id, value, pin, active_low, name, count)

        # Test
        state = State.get_state()

        # Assert
        self.assertIsNotNone(state)
        loaded_meters = state.get_electric_meters()
        loaded_meter = loaded_meters[meter_id]

        self.assertEqual(loaded_meter.value, value)
        self.assertEqual(loaded_meter.pin, pin)
        self.assertEqual(loaded_meter.active_low, active_low)
        self.assertEqual(loaded_meter.name, name)
        self.assertEqual(loaded_meter.count, count)

    def test_load_invalid_syntax_file(self):
        # Setup
        # invalid file
        invalid_file = \
            '''{"next_id" next_id, 
                "electric_meters":[
                    {{"id": {id},
                     "vaue": {value},
                     "count": {count},
                     "nae: "{name}",
                     "pin: {pin},
                     "actie_low": act_low}
                    }}
                ]
            }}'''
        with open(Persistence.STATE_FILE, 'w') as state_file:
            state_file.writelines(invalid_file)

        # Test
        # Assert
        self.assertRaises(Persistence.InvalidStateFileException, State.get_state)

    def test_load_invalid_semantic_file(self):
        # TODO vllt mehrere Test wegen negativen Zahlen und/oder falschem Datentyp
        # Setup
        meter_id = 1
        value = -321
        pin = 123
        active_low = 'invalid_semantics'
        name = 'test'
        count = 456

        create_state_file(meter_id + 1, meter_id, value, pin, active_low, name, count)

        # Test
        # Assert
        self.assertRaises(Persistence.InvalidStateFileException, State.get_state)

    def test_load_missing_file(self):
        # Setup
        if os.path.exists(Persistence.STATE_FILE):
            os.remove(Persistence.STATE_FILE)

        # Test
        state = State.get_state()

        # Assert
        self.assertIsNotNone(state)
        self.assertIsNotNone(state.get_next_id())
        self.assertIsNotNone(state.get_electric_meters())
        self.assertEqual(len(state.get_electric_meters()), 0)


if __name__ == '__main__':
    unittest.main()
