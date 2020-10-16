import unittest
from Database import Database
import os


class DatabaseTest(unittest.TestCase):

    def setUp(self) -> None:
        self.dph = 2
        self.db = Database(self.dph, 3, 48, 30, 12, 3)
        self.db.add_data_src('data1')

    def test_create_database(self):
        db = Database.create_database('test.json')

        self.assertIsNotNone(db)
        self.assertTrue(os.path.exists('test.json'))

    def test_save_load_database(self):
        # Create database and save
        db = Database.create_database('db.json')
        db.add_data_src('data1')
        db.add_data(123)
        # Load data
        db = Database.load_database('db.json')
        # Assert
        self.assertIn(123, db.get_raw())

    def test_add_data_raw(self):

        for i in range(5):
            self.db.add_data(i, 'data1')

        data = self.db.get_raw()
        self.assertEqual(3, len(data['data1']))
        for i in range(2, 5):
            self.assertIn(i, [value for value, time in data['data1']])

    def test_add_data_day(self):
        for i in range((48 + 1) * self.dph):
            self.db.add_data(i, 'data1')

        data = self.db.get_day()

        self.assertEqual(48, len(data['data1']))
        for i in range(1, 48 + 1):
            self.assertIn(i * self.dph + (i * self.dph + 1), [value for value, time in data['data1']])

    def test_add_data_month(self):
        for i in range((30 + 1) * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_month()

        self.assertEqual(30, len(data['data1']))
        for i in range(0, 30):
            self.assertEqual(24, [value for value, time in data['data1']][i])

    def test_add_data_year(self):
        for i in range((365 + 1) * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_year()

        self.assertEqual(12, len(data['data1']))
        for i in range(12):
            self.assertEqual(720, [value for value, time in data['data1']][i])

    def test_add_data_years(self):
        for i in range(3 * 365 * 24 * self.dph):
            self.db.add_data(1/self.dph, 'data1')

        data = self.db.get_years()

        self.assertEqual(3, len(data['data1']))
        for i in range(3):
            self.assertEqual(8760, [value for value, time in data['data1']][i])

    def test_remove_datasource(self):
        self.assertIn('data1', self.db.get_raw().keys())
        self.db.remove_data_src('data1')
        self.assertNotIn('data1', self.db.get_raw().keys())


if __name__ == '__main__':
    unittest.main()
