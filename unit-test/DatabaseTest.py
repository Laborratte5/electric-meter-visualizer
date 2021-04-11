from datetime import datetime, timedelta
import unittest
from Database import Database, Archive
import os


def cleanup() -> None:
    if os.path.isfile('test.json'):
        os.remove('test.json')


class DatabaseTest(unittest.TestCase):

    def setUp(self) -> None:
        self.dph = 2
        with open('test.json', 'w') as f:
            f.write('x')
        self.db = Database('test.json', self.dph, 3, 48, 30, 12, 3)
        self.db.add_data_src('data1')
        self.db.sync_file = False
        self.addCleanup(cleanup)

    def test_create_database(self):
        db = Database.create_database('test.json', self.dph, 3, 48, 30, 12, 3)

        self.assertIsNotNone(db)
        self.assertTrue(os.path.exists('test.json'))

    def test_save_load_database(self):
        # Create database and save
        db = Database.create_database('test.json', self.dph, 3, 48, 30, 12, 3)
        db.sync_file = True
        db.add_data_src('test')
        db.add_data_src('data1')
        db.add_data(123, 'data1')
        # Load data
        db = Database.load_database('test.json')
        # Assert
        self.assertIn('data1', db.datasources.keys())
        self.assertIn('test', db.datasources.keys())
        self.assertEqual(self.dph, db.dph)
        self.assertEqual(3, db.keep_raw)
        self.assertEqual(48, db.keep_day)
        self.assertEqual(30, db.keep_month)
        self.assertEqual(12, db.keep_year)
        self.assertEqual(3, db.keep_years)
        self.assertIn(123, [items['value'] for items in db.get_raw()['data1']])
        self.assertNotEqual(0, len([timestamp for value, timestamp in db.get_raw()['data1']]))
        # TODO vllt. bessere/schönere Art and timestamp zu kommen
        self.assertEqual(type(datetime.now()), type([item['timestamp'] for item in db.get_raw()['data1']][0]))

    def test_add_data_raw(self):

        for i in range(5):
            self.db.add_data(i, 'data1')

        data = self.db.get_raw()
        self.assertEqual(3, len(data['data1']))
        for i in range(2, 5):
            self.assertIn(i, [items['value'] for items in data['data1']])

    def test_add_data_day(self):
        for i in range((48 + 1) * self.dph):
            self.db.add_data(i, 'data1')

        data = self.db.get_day()

        self.assertEqual(48 + 1, len(data['data1']))
        for i in range(1, 48 + 1):
            self.assertIn(i * self.dph + (i * self.dph + 1), [items['value'] for items in data['data1']])

    def test_add_data_month(self):
        for i in range((30 + 1) * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_month()

        self.assertEqual(30 + 1, len(data['data1']))
        for i in range(0, 30):
            self.assertEqual(24, [items['value'] for items in data['data1']][i])

    def test_add_data_year(self):
        for i in range((365 + 1) * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_year()

        self.assertEqual(12 + 1, len(data['data1']))
        for i in range(12):
            self.assertEqual(720, [items['value'] for items in data['data1']][i])

    def test_add_data_years(self):
        for i in range(3 * 365 * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_years()

        self.assertEqual(3 + 1, len(data['data1']))
        for i in range(3):
            self.assertEqual(8760, [items['value'] for items in data['data1']][i])

    def test_remove_datasource(self):
        self.assertIn('data1', self.db.get_raw().keys())
        self.db.remove_data_src('data1')
        self.assertNotIn('data1', self.db.get_raw().keys())


class GetDataDatabaseTest(unittest.TestCase):

    def setUp(self) -> None:
        self.dph = 2
        with open('test.json', 'w') as f:
            f.write('x')
        self.db = Database('test.json', self.dph, 3, 48, 30, 12, 3)
        self.datasrc = 'data1'
        self.db.add_data_src(self.datasrc)
        self.db.sync_file = False

        self.datasource = Archive(self.dph, 3, 48, 30, 12, 3)

        self.datasource.raw = [(1, datetime(2020, 10, 30, 12, 00)),
                               (2, datetime(2020, 10, 30, 12, 15)),
                               (3, datetime(2020, 10, 30, 12, 30)),
                               (4, datetime(2020, 10, 30, 12, 45)),

                               (5, datetime(2020, 10, 30, 13, 00)),
                               (6, datetime(2020, 10, 30, 13, 15)),
                               (7, datetime(2020, 10, 30, 13, 30)),
                               (8, datetime(2020, 10, 30, 13, 45)),
                               ]
        self.datasource.day = [(hour * 10, datetime(2020, 10, hour//24 + 1, hour % 24, 00))
                               for hour in range(48)]
        self.datasource.month = [(day * 10, datetime(2020, day//30 + 3, day % 30 + 1, 00, 00))
                                 for day in range(60)]
        self.datasource.year = [(month * 10, datetime(2020, month + 1, 1, 00, 00))
                                for month in range(12)]
        self.datasource.years = [(year * 10, datetime(year + 1, 1, 1, 00, 00))
                                 for year in range(3)]

        self.db.datasources[self.datasrc] = self.datasource

        self.addCleanup(cleanup)

    # TODO test exceed upper bound
    # TODO test beneath lower bound
    # TODO test outside of data bounds

    def test_get_raw_since(self):
        # Test
        data = self.db.get_raw(since=datetime(2020, 10, 30, 13, 00))[self.datasrc]

        # Assert
        self.assertEqual(4, len(data))
        pairs = zip([self.datasource.raw[i] for i in range(4, 8)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_raw_until(self):
        # Test
        data = self.db.get_raw(until=datetime(2020, 10, 30, 13, 00))[self.datasrc]

        # Assert
        self.assertEqual(5, len(data))
        pairs = zip([self.datasource.raw[i] for i in range(0, 5)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_raw_until_since(self):
        # Test
        data = self.db.get_raw(since=datetime(2020, 10, 30, 12, 30),
                               until=datetime(2020, 10, 30, 13, 15))[self.datasrc]

        # Assert
        self.assertEqual(4, len(data))
        pairs = zip([self.datasource.raw[i] for i in range(2, 6)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            print(expected, actual)
            self.assertEqual(expected, actual)

    def test_get_raw_invalid_until_since(self):
        # Since datetime is after until date time
        self.assertRaises(ValueError, self.db.get_raw,
                          until=datetime(2020, 10, 30, 12, 15), since=datetime(2020, 10, 30, 13, 30))

    def test_get_day_since(self):
        data = self.db.get_day(since=datetime(2020, 10, 1, 15, 00))[self.datasrc]

        # Assert
        self.assertEqual(34, len(data))
        pairs = zip([self.datasource.day[i] for i in range(15, 48)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_day_until(self):
        data = self.db.get_day(until=datetime(2020, 10, 2, 12, 00))[self.datasrc]

        # Assert
        self.assertEqual(37, len(data))
        pairs = zip([self.datasource.day[i] for i in range(0, 37)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_day_until_since(self):
        data = self.db.get_day(since=datetime(2020, 10, 1, 12, 00), until=datetime(2020, 10, 2, 12, 00))[self.datasrc]

        # Assert
        self.assertEqual(25, len(data))
        pairs = zip([self.datasource.day[i] for i in range(12, 36)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_day_invalid_until_since(self):
        # Since datetime is after until date time
        self.assertRaises(ValueError, self.db.get_day,
                          until=datetime(2020, 10, 1, 12, 00), since=datetime(2020, 10, 2, 12, 00))

    def test_get_month_since(self):
        data = self.db.get_month(since=datetime(2020, 3, 15, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(47, len(data))
        pairs = zip([self.datasource.month[i] for i in range(14, 60)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_month_until(self):
        data = self.db.get_month(until=datetime(2020, 4, 15, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(45, len(data))
        pairs = zip([self.datasource.month[i] for i in range(0, 45)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_month_until_since(self):
        data = self.db.get_month(since=datetime(2020, 3, 15, 0, 00),
                               until=datetime(2020, 4, 15, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(31, len(data))
        pairs = zip([self.datasource.month[i] for i in range(14, 45)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_month_invalid_until_since(self):
        self.assertRaises(ValueError, self.db.get_month,
                          until=datetime(2020, 3, 15, 0, 00), since=datetime(2020, 4, 15, 0, 00))

    def test_get_year_since(self):
        data = self.db.get_year(since=datetime(2020, 6, 1, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(8, len(data))
        pairs = zip([self.datasource.year[i] for i in range(5, 12)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_year_until(self):
        data = self.db.get_year(until=datetime(2020, 6, 1, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(6, len(data))
        pairs = zip([self.datasource.year[i] for i in range(0, 6)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_year_until_since(self):
        data = self.db.get_year(since=datetime(2020, 3, 1, 0, 00),
                                until=datetime(2020, 9, 1, 0, 00))[self.datasrc]

        # Assert
        self.assertEqual(7, len(data))
        pairs = zip([self.datasource.year[i] for i in range(2, 9)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_year_invalid_until_since(self):
        self.assertRaises(ValueError, self.db.get_year,
                          until=datetime(2020, 3, 1, 0, 00), since=datetime(2020, 9, 1, 0, 00))

    def test_get_years_since(self):
        data = self.db.get_years(since=datetime(2, 1, 1, 00, 00))[self.datasrc]

        # Assert
        self.assertEqual(3, len(data))
        pairs = zip([self.datasource.years[i] for i in range(1, 3)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_years_until(self):
        data = self.db.get_years(until=datetime(2, 1, 1, 00, 00))[self.datasrc]

        # Assert
        self.assertEqual(2, len(data))
        pairs = zip([self.datasource.years[i] for i in range(0, 2)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_years_until_since(self):
        data = self.db.get_years(since=datetime(2, 1, 1, 00, 00), until=datetime(2, 1, 1, 00, 00))[self.datasrc]

        # Assert
        self.assertEqual(1, len(data))
        pairs = zip([self.datasource.years[i] for i in range(1, 2)],
                    [(data['value'], data['timestamp']) for data in data])
        for expected, actual in pairs:
            self.assertEqual(expected, actual)

    def test_get_years_invalid_until_since(self):
        self.assertRaises(ValueError, self.db.get_month,
                          until=datetime(1, 1, 1, 0, 00), since=datetime(2, 1, 1, 0, 0))


if __name__ == '__main__':
    unittest.main()
