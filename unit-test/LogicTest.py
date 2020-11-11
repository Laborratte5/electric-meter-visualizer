import string
import unittest
import random
from datetime import datetime

from ElectricMeterMockup import ElectricMeterMockup
from Logic import Logic


class DatabaseLogicTestMock:

    def __init__(self):
        self.data_sources = {}

    def add_data_src(self, data_src_name):
        self.data_sources[data_src_name] = []

    def remove_data_src(self, data_src_name):
        del self.data_sources[data_src_name]

    def add_data(self, data, data_src):
        self.data_sources[data_src].append(data)

    def get_raw(self, delta=0):
        return self.data_sources


class DatabaseLogicGetTestMock:

    def get_raw(self, delta=0):
        return {1: [{'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 00)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 15)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 30)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 45)},

                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 00)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 15)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 30)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 45)},
                        ]}

    def get_day(self, delta=0):
        return {1: [{'value': hour * 10, 'timestamp': datetime(2020, 10, hour//24 + 1, hour % 24, 00)}
                    for hour in range(48)]}

    def get_month(self, delta=0):
        # Start with March to skip February because of 28 day instead of 30 or 31
        return {1: [{'value': day * 10, 'timestamp': datetime(2020, day//30 + 3, day % 30 + 1, 00, 00)}
                    for day in range(60)]}

    def get_year(self, delta=0):
        return {1: [{'value': month * 10, 'timestamp': datetime(2020, month + 1, 1, 00, 00)}
                        for month in range(12)]}

    def get_years(self, delta=0):
        return {1: [{'value': year * 10, 'timestamp': datetime(year + 1, 1, 1, 00, 00)}
                    for year in range(3)]}


class ElectricMeterTestMock:

    def __init__(self, amount=0):
        self.amount = amount

    def set_amount(self, amount):
        self.amount = amount

    def get_amount(self):
        return self.amount

    def reset(self):
        pass


# Test every method in Logic except get_dataXY() methods
class LogicTest(unittest.TestCase):

    def setUp(self):
        self.logic = Logic(True)
        self.db_mock = DatabaseLogicTestMock()
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
        self.logic._next_id = electric_meter_id
        self.db_mock.add_data_src(electric_meter_id)

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
        self.logic._next_id = electric_meter_id

        # Change Electric Meter
        self.logic.change_electric_meter(electric_meter_id, 100, 500, True, 'changed_em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(electric_meter_id)
        self.assertEqual(em.value, 100)
        self.assertEqual(em.pin, 500)
        self.assertEqual(em.active_low, True)
        self.assertEqual(em.name, 'changed_em1')

    def test_read_electric_meters(self):
        # Setup Electric Meter
        em1_id = 0
        em2_id = 1
        em1 = ElectricMeterTestMock(amount=1)
        em2 = ElectricMeterTestMock(amount=10)
        self.logic.electric_meters[em1_id] = em1
        self.logic.electric_meters[em2_id] = em2
        self.logic._next_id = 1
        # Setup Database
        self.db_mock.add_data_src(em1_id)
        self.db_mock.add_data_src(em2_id)

        # Test _read_electric_meters()
        for i in range(10):
            em1.set_amount(i)
            em2.set_amount(i*10)
            self.logic._read_electric_meters()

        # Assert database values
        for i in range(10):
            self.assertIn(i, self.db_mock.get_raw()[em1_id])
            self.assertIn(i*10, self.db_mock.get_raw()[em2_id])


# Only test get_dataXY() methods
class LogicGetTest(unittest.TestCase):

    def setUp(self):
        self.logic = Logic(True)
        self.electric_meter_name = 'em1'
        self.logic.add_electric_meter(1, 1, False, self.electric_meter_name)
        self.db_mock = DatabaseLogicGetTestMock()
        self.logic.database = self.db_mock

    def test_get_raw(self):
        raw = self.logic.get_raw()

        # Assertion
        self.assertIn(self.electric_meter_name, raw.keys())
        for idx, data_point in enumerate(raw[self.electric_meter_name]):
            self.assertEqual(data_point['value'], self.db_mock.get_raw()[1][idx]['value'])
            self.assertEqual(data_point['timestamp'], self.db_mock.get_raw()[1][idx]['timestamp'])

    def test_get_day(self):
        day = self.logic.get_day()

        # Assertion
        self.assertIn(self.electric_meter_name, day.keys())
        for idx, data_point in enumerate(day[self.electric_meter_name]):
            self.assertEqual(data_point['value'], self.db_mock.get_day()[1][idx]['value'])
            self.assertEqual(data_point['timestamp'], self.db_mock.get_day()[1][idx]['timestamp'])

    def test_get_week(self):
        # TODO
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
