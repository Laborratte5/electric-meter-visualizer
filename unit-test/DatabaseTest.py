import time
from datetime import datetime
import os
import subprocess
import unittest

from Database import Database


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test.rrd'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_create_db(self):
        db = Database.create(self.test_db, 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        self.assertNotEqual(db, None)
        self.assertTrue(os.path.isfile(self.test_db))

    def test_not_override_existing_db(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '5',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        exception = None
        try:
            Database.create(self.test_db, 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        except FileExistsError as e:
            exception = e
        self.assertIsInstance(exception, FileExistsError)

    def test_load_db(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '5',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0

        db = Database.load(self.test_db)
        self.assertIsNotNone(db)
        # TODO

    def test_add_data(self):
        #db = Database.create(self.test_db, 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '5',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        db = Database(self.test_db)
        data = db.get_data()['LAST']['em1']
        prev_len = len(data)

        db.add_data([3])
        time.sleep(6)
        db.add_data([3])

        data = db.get_data()['LAST']['em1']
        crnt_len = len(data)
        self.assertGreater(crnt_len, prev_len)

    def test_get_data(self):
        #db = Database.create('test.rrd', 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '5',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        for i in range(3):
            assert subprocess.call(['rrdtool','update', self.test_db,'N:100']) == 0
            time.sleep(5)

        epoch = time.mktime(datetime.today().timetuple())
        db = Database(self.test_db)
        data = db.get_data()['LAST']['em1']
        filtered = [value for time_stamp, value in data if epoch - 15 < time_stamp < epoch + 15]
        self.assertTrue(100 in filtered)

    def test_parse_result(self):
        pass


if __name__ == '__main__':
    unittest.main()
