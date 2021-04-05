import os
import string
import unittest
import random
from datetime import datetime

from ElectricMeterMockup import ElectricMeterMockup
from Logic import Logic


class ConfigMock:

    def get_next_id(self):
        return 0

    def get_electric_meters(self):
        return {}

    def get_database_file(self):
        return 'database.json'

    def get_data_per_hour(self):
        return 3600

    def get_keep_raw(self):
        return 10

    def get_keep_day(self):
        return 48

    def get_keep_month(self):
        return 30

    def get_keep_year(self):
        return 12

    def get_keep_years(self):
        return 3


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
        return {10: [{'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 00)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 15)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 30)},
                        {'value': 1, 'timestamp': datetime(2020, 10, 30, 12, 45)},

                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 00)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 15)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 30)},
                        {'value': 2, 'timestamp': datetime(2020, 10, 30, 13, 45)},
                        ]}

    def get_day(self, delta=0):
        return {10: [{'value': hour * 10, 'timestamp': datetime(2020, 10, hour//24 + 1, hour % 24, 00)}
                    for hour in range(48)]}

    def get_month(self, delta=0):
        # Start with March to skip February because of 28 day instead of 30 or 31
        return {10: [{'value': day * 10, 'timestamp': datetime(2020, day//30 + 3, day % 30 + 1, 00, 00)}
                    for day in range(60)]}

    def get_year(self, delta=0):
        return {10: [{'value': month * 10, 'timestamp': datetime(2020, month + 1, 1, 00, 00)}
                        for month in range(12)]}

    def get_years(self, delta=0):
        return {10: [{'value': year * 10, 'timestamp': datetime(year + 1, 1, 1, 00, 00)}
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


class StateMock:
    @classmethod
    def get_state(cls):
        return StateMock()

    def __init__(self):
        # Initialize with default values
        self.next_id = 10
        self.electric_meters = {}

    def get_next_id(self):
        return self.next_id

    def set_next_id(self, next_id):
        self.next_id = next_id

    def get_electric_meters(self):
        return self.electric_meters

    def set_electric_meters(self, electric_meters):
        self.electric_meters = electric_meters


def cleanup() -> None:
    if os.path.isfile('database.json'):
        os.remove('database.json')


# Test every method in Logic except get_dataXY() methods
class LogicTest(unittest.TestCase):

    def setUp(self):
        self.logic = Logic(ConfigMock(), True)
        self.db_mock = DatabaseLogicTestMock()
        self.logic.database = self.db_mock
        self.state_mock = StateMock()
        self.logic.state = self.state_mock
        self.addCleanup(cleanup)

    def test_add_electric_meter(self):
        pre_add_len = len(self.state_mock.electric_meters)

        # Create random values
        value = random.random() * random.randint(1, 100)
        pin = random.randint(1, 10)
        active_low = random.choice([True, False])
        name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))

        # Add electric meter
        new_meter, id = self.logic.add_electric_meter(value, pin, active_low, name)

        # Assertion
        self.assertGreater(len(self.state_mock.electric_meters), pre_add_len)

        self.assertEqual(value, new_meter.value)
        self.assertEqual(pin, new_meter.pin)
        self.assertEqual(active_low, new_meter.active_low)
        self.assertEqual(name, new_meter.name)

        self.assertEqual(new_meter, self.logic.get_electric_meter(id))

    def test_add_invalid_meter(self):
        value = -3
        pin = -2
        active_low = False
        name = ''

        self.assertRaises(ValueError, self.logic.add_electric_meter, value, pin, active_low, name)

    def test_remove_electric_meter(self):
        # Add electric meter
        electric_meter_id = 0
        electric_meter = ElectricMeterMockup(1, 1, False, 'electric meter to be removed')
        self.state_mock.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id
        self.db_mock.add_data_src(electric_meter_id)

        pre_remove_len = len(self.state_mock.electric_meters)
        # Remove electric meter
        removed_meter = self.logic.remove_electric_meter(electric_meter_id)

        # Check if electric meter has been removed
        self.assertGreater(pre_remove_len, len(self.state_mock.electric_meters))
        self.assertNotIn(electric_meter, self.state_mock.electric_meters.values())
        # Check if correct electric meter has been removed
        self.assertEqual(removed_meter, electric_meter)

    def test_remove_not_existing_meter(self):
        invalid_meter_id = -100

        self.assertRaises(KeyError, self.logic.remove_electric_meter, invalid_meter_id)

    def test_change_electric_meter(self):
        # Setup
        electric_meter = ElectricMeterMockup(10, 1, False, 'em1')
        electric_meter_id = 10
        new_value = 5
        new_pin = 6
        self.state_mock.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id

        # Change Electric Meter
        changed_meter = self.logic.change_electric_meter(electric_meter_id, new_value, new_pin, True, 'changed_em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(electric_meter_id)
        self.assertEqual(new_value, em.value)
        self.assertEqual(new_value, changed_meter.value)
        self.assertEqual(new_pin, em.pin)
        self.assertEqual(new_pin, changed_meter.pin)
        self.assertEqual(True, em.active_low)
        self.assertEqual(True, changed_meter.active_low)
        self.assertEqual('changed_em1', em.name)
        self.assertEqual('changed_em1', changed_meter.name)

    def test_change_electric_meter_no_change(self):
        # Setup
        electric_meter = ElectricMeterMockup(10, 1, False, 'em1')
        electric_meter_id = 10
        self.state_mock.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id

        # Change Electric Meter
        changed_meter = self.logic.change_electric_meter(electric_meter_id, 10, 1, False, 'em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(electric_meter_id)
        self.assertIsNone(changed_meter)
        self.assertEqual(10, em.value)
        self.assertEqual(1, em.pin)
        self.assertEqual(False, em.active_low)
        self.assertEqual('em1', em.name)

    def test_partial_change_electric_meter_no_change(self):
        # Setup
        electric_meter = ElectricMeterMockup(10, 1, False, 'em1')
        electric_meter_id = 10
        self.state_mock.electric_meters[electric_meter_id] = electric_meter
        self.logic._next_id = electric_meter_id

        # Change Electric Meter
        changed_meter = self.logic.change_electric_meter(electric_meter_id, 10, None, None, 'em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(electric_meter_id)
        self.assertIsNone(changed_meter)
        self.assertEqual(10, em.value)
        self.assertEqual(1, em.pin)
        self.assertEqual(False, em.active_low)
        self.assertEqual('em1', em.name)

    def test_change_not_existing_meter(self):
        invalid_meter_id = -100

        # Assert
        self.assertRaises(KeyError, self.logic.change_electric_meter, invalid_meter_id)

    def test_invalid_change_on_meter(self):
        # Setup
        self.state_mock.electric_meters[0] = ElectricMeterMockup(1, 1, False, 'meter1')
        value = -3
        pin = -2
        active_low = False
        name = ''

        # Assert
        self.assertRaises(ValueError, self.logic.change_electric_meter, 0, value, pin, active_low, name)

    def test_read_electric_meters(self):
        # Setup Electric Meter
        em1_id = 0
        em2_id = 1
        em1 = ElectricMeterTestMock(amount=1)
        em2 = ElectricMeterTestMock(amount=10)
        self.state_mock.electric_meters[em1_id] = em1
        self.state_mock.electric_meters[em2_id] = em2
        self.state_mock.next_id = 1
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
        self.logic = Logic(ConfigMock(), True)
        self.logic.state = StateMock()
        self.electric_meter_name = 'em1'
        self.logic.add_electric_meter(1, 1, False, self.electric_meter_name)
        self.db_mock = DatabaseLogicGetTestMock()
        self.logic.database = self.db_mock
        self.addCleanup(cleanup)

    def test_get_electric_meters(self):
        # Setup
        test_meter1 = ElectricMeterMockup(5, 1, False, 'test_meter')
        test_meter2 = ElectricMeterMockup(3, 2, False, 'second_test_meter')
        self.logic.state.set_electric_meters({
            10: test_meter1,
            11: test_meter2
        })

        # Test
        meters = self.logic.get_electric_meters()

        # Assertion
        self.assertIn((10, test_meter1), meters)
        self.assertIn((11, test_meter2), meters)

    def test_get_raw(self):
        raw = self.logic.get_raw()
        meter_id = 10

        # Assertion
        self.assertIn(self.electric_meter_name, raw.keys())
        self.assertEqual(len(self.db_mock.get_raw()[meter_id]), len(raw[self.electric_meter_name]))
        for idx, data_point in enumerate(raw[self.electric_meter_name]):
            self.assertEqual(self.db_mock.get_raw()[meter_id][idx]['value'], data_point['value'])
            self.assertEqual(self.db_mock.get_raw()[meter_id][idx]['timestamp'], data_point['timestamp'])

    def test_get_day(self):
        day = self.logic.get_day()
        meter_id = 10

        # Assertion
        self.assertIn(self.electric_meter_name, day.keys())
        self.assertEqual(len(self.db_mock.get_day()[meter_id]), len(day[self.electric_meter_name]))
        for idx, data_point in enumerate(day[self.electric_meter_name]):
            self.assertEqual(self.db_mock.get_day()[meter_id][idx]['value'], data_point['value'])
            self.assertEqual(self.db_mock.get_day()[meter_id][idx]['timestamp'], data_point['timestamp'])

    def test_get_month(self):
        month = self.logic.get_month()
        meter_id = 10

        # Assertion
        self.assertIn(self.electric_meter_name, month.keys())
        self.assertEqual(len(self.db_mock.get_month()[meter_id]), len(month[self.electric_meter_name]))
        for idx, data_point in enumerate(month[self.electric_meter_name]):
            self.assertEqual(self.db_mock.get_month()[meter_id][idx]['value'], data_point['value'])
            self.assertEqual(self.db_mock.get_month()[meter_id][idx]['timestamp'], data_point['timestamp'])

    def test_get_year(self):
        year = self.logic.get_year()
        meter_id = 10

        # Assertion
        self.assertIn(self.electric_meter_name, year.keys())
        self.assertEqual(len(self.db_mock.get_year()[meter_id]), len(year[self.electric_meter_name]))
        for idx, data_point in enumerate(year[self.electric_meter_name]):
            self.assertEqual(self.db_mock.get_year()[meter_id][idx]['value'], data_point['value'])
            self.assertEqual(self.db_mock.get_year()[meter_id][idx]['timestamp'], data_point['timestamp'])

    def test_get_years(self):
        years = self.logic.get_years()
        meter_id = 10

        # Assertion
        self.assertIn(self.electric_meter_name, years.keys())
        self.assertEqual(len(self.db_mock.get_years()[meter_id]), len(years[self.electric_meter_name]))
        for idx, data_point in enumerate(years[self.electric_meter_name]):
            self.assertEqual(self.db_mock.get_years()[meter_id][idx]['value'], data_point['value'])
            self.assertEqual(self.db_mock.get_years()[meter_id][idx]['timestamp'], data_point['timestamp'])


if __name__ == '__main__':
    unittest.main()
