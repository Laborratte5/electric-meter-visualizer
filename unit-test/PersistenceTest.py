import unittest
import os
import random
import json

import Persistence
from ElectricMeterMockup import ElectricMeterMockup
from Persistence import State


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.isfile(Persistence.STATE_FILE):
            os.remove(Persistence.STATE_FILE)
        pass

    def test_get_state(self):
        state = State.get_state()
        self.assertIsNotNone(state)

    def test_save_next_id(self):
        # Setup
        next_id = random.randint()
        state = State.get_state()

        # Test
        state.set_next_id(next_id)

        # Assert
        with open(Persistence.STATE_FILE) as state_file:
            obj = json.loads(state_file)
            self.assertEqual(obj['next-id'], str(next_id))

    def test_load_next_id(self):
        # TODO
        pass

    def test_save_electric_meter(self):
        # Setup
        value = 321
        pin = 123
        active_low = False
        name = 'test'
        electric_meter = ElectricMeterMockup(value, pin, active_low, name)
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

    def test_load_electric_meter(self):
        # TODO
        pass

    def test_load_invalid_file(self):
        # TODO
        pass

    def test_load_missing_file(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
