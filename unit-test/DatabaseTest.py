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
        self.db.add_data_src('data1')
        self.db.sync_file = False

        datasource = Archive(self.dph, 3, 48, 30, 12, 3)

        now = datetime.now()

        datasource.raw = [(i, now + timedelta(minutes=60 / self.dph)) for i in range(datasource.keep_raw)]
        datasource.day = [{'value': hour * 10, 'timestamp': datetime(2020, 10, hour//24 + 1, hour % 24, 00)}
                          for hour in range(48)]
        datasource.month = [{'value': day * 10, 'timestamp': datetime(2020, day//30 + 3, day % 30 + 1, 00, 00)}
                            for day in range(60)]
        datasource.year = [{'value': month * 10, 'timestamp': datetime(2020, month + 1, 1, 00, 00)}
                           for month in range(12)]
        datasource.years = [{'value': year * 10, 'timestamp': datetime(year + 1, 1, 1, 00, 00)}
                            for year in range(3)]

        self.db.datasources['data1'] = datasource

        self.addCleanup(cleanup)


if __name__ == '__main__':
    unittest.main()
