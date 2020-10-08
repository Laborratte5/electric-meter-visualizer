import unittest
from Database import Database

class MyTestCase(unittest.TestCase):

    def test_create_database(self):

        pass

    def test_load_database(self):
        pass

    def test_add_data_day(self):
        db = Database(24, 24,
                      7*24, 7,
                      30 * 24, 30,
                      365 * 24, 365,
                      3)
        db.add_data_src('data1')
        # TODO in schleife hinzufügen
        for i in range(24):
            db.add_data(i, 'data1')

        data = db.get_day()

        # TODO so richtig?
        for i in range(24):
            self.assertIn(i, data['data1'])

    def test_add_data_week(self):
        db = Database(24, 24,
                      7*24, 7,
                      30 * 24, 30,
                      365 * 24, 365,
                      3)
        db.add_data_src('data1')
        # TODO in schleife hinzufügen
        for i in range(7*24):
            db.add_data(i, 'data1')

        data = db.get_week()

        # TODO so richtig?
        for i in range(1, 8):
            value = i * 7
            self.assertIn(value, data['data1'])

    def test_add_data_month(self):
        db = Database(24, 24,
                      7*24, 7,
                      30 * 24, 30,
                      365 * 24, 365,
                      3)
        db.add_data_src('data1')
        # TODO in schleife hinzufügen
        for i in range(30 * 7 * 24):
            db.add_data(i, 'data1')

        data = db.get_month()

        # TODO so richtig?
        for i in range(1, 31):
            value = i * 30
            self.assertIn(value, data['data1'])

    def test_add_data_year(self):
        db = Database(24, 24,
                      7 * 24, 7,
                      30 * 24, 30,
                      365 * 24, 365,
                      3)
        db.add_data_src('data1')
        # TODO in schleife hinzufügen
        for i in range(365 * 24):
            db.add_data(i, 'data1')

        data = db.get_month()

        # TODO so richtig?
        for i in range(1, 366):
            value = i * 30
            self.assertIn(value, data['data1'])

    def test_add_data_years(self):
        db = Database(24, 24,
                      7 * 24, 7,
                      30 * 24, 30,
                      365 * 24, 365,
                      3)
        db.add_data_src('data1')
        # TODO in schleife hinzufügen
        for i in range(3 * 365 * 24):
            db.add_data(i, 'data1')

        data = db.get_month()

        # TODO so richtig?
        for i in range(1, 31):
            value = i * 30
            self.assertIn(value, data['data1'])

if __name__ == '__main__':
    unittest.main()
