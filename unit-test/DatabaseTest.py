import unittest
from Database import Database


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.db = Database(1, 3, 48, 14, 30, 12)
        self.db.add_data_src('data1')

    def test_create_database(self):

        pass

    def test_load_database(self):
        pass

    def test_add_data_raw(self):

        for i in range(5):
            self.db.add_data(i, 'data1')

        data = self.db.get_raw()
        self.assertEqual(3, len(data['data1']))
        for i in range(2, 5):
            self.assertIn(i, [value for value, time in data['data1']])

    def test_add_data_day(self):
        for i in range(49):
            self.db.add_data(i, 'data1')

        data = self.db.get_day()

        self.assertEqual(48, len(data['data1']))
        for i in range(1, 49):
            self.assertIn(i, [value for value, time in data['data1']])

    def test_add_data_week(self):
        for i in range(14 * 24 + 1):
            self.db.add_data(i//24, 'data1')

        data = self.db.get_week()

        self.assertEqual(14, len(data['data1']))
        for i in range(24):
            self.assertIn(i//24, [value for value, time in data['data1']])

    def test_add_data_month(self):
        for i in range(30 * 24 + 1):
            self.db.add_data(i//24, 'data1')

        data = self.db.get_month()

        # TODO so richtig?
        self.assertEqual(30, len(data['data1']))
        for i in range(1, 30 * 24):
            self.assertIn(i//24, [value for value, time in data['data1']])

    def test_add_data_year(self):
        for i in range(365 * 24 + 1):
            self.db.add_data(i, 'data1')

        data = self.db.get_year()

        # TODO so richtig?
        self.assertEqual(12, len(data['data1']))
        for i in range(1, 365 * 24):
            self.assertIn(i, [value for value, time in data['data1']])

    def test_add_data_years(self):
        # TODO in schleife hinzufügen
        # TODO nachrechnen und assertion anpassen
        for i in range(1, 3 * 365 * 24 + 1):
            self.db.add_data(i, 'data1')

        data = self.db.get_years()

        # TODO so richtig?
        self.assertEqual(3, len(data['data1']))
        for i in range(1, 3 * 365 * 24):
            self.assertIn(i, [value for value, time in data['data1']])


if __name__ == '__main__':
    unittest.main()
