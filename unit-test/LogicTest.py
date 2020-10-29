import string
import unittest
import random

from ElectricMeterMockup import ElectricMeterMockup
from Logic import Logic


# TODO überarbeiten (Logik mit neuer Datenbank)
class DatabaseMock:

    def __init__(self):
        pass

    def add_data_src(self, data_src_name):
        pass

    def remove_data_src(self, data_src_name):
        pass

    def add_data(self, data, data_src):
        pass

    def get_raw(self, delta=0):
        pass

    def get_day(self, delta=0):
        pass

    def get_month(self, delta=0):
        pass

    def get_year(self, delta=0):
        pass

    def get_years(self, delta=0):
        pass


class LogicTest(unittest.TestCase):

    def setUp(self):
        self.logic = Logic(True)
        self.db_mock = DatabaseMock()
        self.logic.database = self.db_mock

    def test_add_electric_meter(self):
        pre_add_len = len(self.logic.electric_meters)

        # Create random values
        value = random.random() * random.randint(1, 100)
        pin = random.randint(1, 10)
        active_low = random.choice([True, False])
        name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))

        # Add electric meter
        new_meter, id = self.logic.add_electric_meter(value, pin, active_low, name)

        # Assertion
        self.assertGreater(len(self.logic.electric_meters), pre_add_len)

        self.assertEqual(value, new_meter.value)
        self.assertEqual(pin, new_meter.pin)
        self.assertEqual(active_low, new_meter.active_low)
        self.assertEqual(name, new_meter.name)

        self.assertEqual(new_meter, self.logic.get_electric_meter(id))

    def test_remove_electric_meter(self):
        # Add electric meter
        electric_meter_id = 0
        electric_meter = ElectricMeterMockup(1, 1, False, 'electric meter to be removed')
        self.logic.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id + 1

        pre_remove_len = len(self.logic.electric_meters)
        # Remove electric meter
        removed_meter = self.logic.remove_electric_meter(electric_meter_id)

        # Check if electric meter has been removed
        self.assertGreater(pre_remove_len, len(self.logic.electric_meters))
        self.assertNotIn(electric_meter, self.logic.electric_meters.values())
        # Check if correct electric meter has been removed
        self.assertEqual(removed_meter, electric_meter)

    def test_change_electric_meter(self):
        # Setup
        electric_meter = ElectricMeterMockup(10, 0, False, 'em1')
        electric_meter_id = 10
        self.logic.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id + 1

        # Change Electric Meter
        self.logic.change_electric_meter(electric_meter_id, 100, 500, True, 'changed_em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(electric_meter_id)
        self.assertEqual(em.value, 100)
        self.assertEqual(em.pin, 500)
        self.assertEqual(em.active_low, True)
        self.assertEqual(em.name, 'changed_em1')

    def test_read_electric_meters(self):
        # TODO
        # _read_electric_meters fragt alle electric meter ab und speichert deren Werte in die Datenbank
        self.assertTrue(False)
        pass

    def test_get_raw(self):
        # TODO
        self.assertTrue(False)
        pass

    def test_get_day(self):
        # TODO
        self.assertTrue(False)
        pass

    def test_get_week(self):
        # TODO
        self.assertTrue(False)
        pass

    def test_get_month(self):
        # TODO
        self.assertTrue(False)
        pass

    def test_get_year(self):
        # TODO
        self.assertTrue(False)
        pass

    def test_get_years(self):
        # TODO
        self.assertTrue(False)
        pass


if __name__ == '__main__':
    unittest.main()
