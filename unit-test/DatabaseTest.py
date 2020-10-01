import time
from datetime import datetime
import os
import subprocess
import unittest

import rrdtool as rrd
from Database import Database
from Database import Datasource as DS
from Database import RoundRobinArchive as RRA


# TODO try to write tests without time.sleep(x)
class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test.rrd'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_create_db(self):
        datasource = [DS('em1','GAUGE', 10)]
        rra = [RRA('LAST', 0.5, 1, 10)]
        db = Database.create(self.test_db, 5, datasource, rra)
        self.assertNotEqual(db, None)
        self.assertTrue(os.path.isfile(self.test_db))

    def test_not_override_existing_db(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        exception = None
        try:
            Database.create(self.test_db, 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        except FileExistsError as e:
            exception = e
            # TODO self.assertRaises(xyz)
        self.assertIsInstance(exception, FileExistsError)

    def test_load_db(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0

        db = Database.load(self.test_db)
        self.assertIsNotNone(db)
        # TODO

    def test_add_data(self):
        #db = Database.create(self.test_db, 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        db = Database(self.test_db)
        data = db.get_data()['LAST']['em1']
        prev_len = len(data)

        db.add_data([3])
        time.sleep(1)
        db.add_data([3])

        data = db.get_data()['LAST']['em1']
        crnt_len = len(data)
        self.assertGreater(crnt_len, prev_len)

    def test_get_data(self):
        #db = Database.create('test.rrd', 5, ['DS:em1:GAUGE:10:U:U'], ['RRA:LAST:0.5:1:10'])
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        for i in range(3):
            assert subprocess.call(['rrdtool','update', self.test_db,'N:100']) == 0
            time.sleep(1)

        epoch = time.mktime(datetime.today().timetuple())
        db = Database(self.test_db)
        data = db.get_data()['LAST']['em1']
        filtered = [value for time_stamp, value in data if epoch - 15 < time_stamp < epoch + 15]
        self.assertTrue(100 in filtered)

    def test_add_data_source(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        # Test if other datasources exists
        assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:0:0']) != 0

        # Add datasource
        db = Database(self.test_db)
        db.add_data_source(DS('ds2', 'GAUGE', '10'))
        time.sleep(1)

        # Test if datasource exists
        code = subprocess.call(['rrdtool', 'update', self.test_db, 'N:0:0'])
        self.assertEqual(code, 0)

    def test_remove_data_source(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'DS:em2:GAUGE:10:U:U', 'RRA:LAST:0.5:1:10']) == 0
        # Test if datasource exists
        assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:0:0']) == 0

        # Remove datasource
        db = Database(self.test_db)
        db.remove_data_source(DS('em1', 'GAUGE', '10'))
        time.sleep(1)

        # Test if datasource was removed
        code = subprocess.call(['rrdtool', 'update', self.test_db, 'N:0:0'])
        self.assertNotEqual(code, 0)

    def test_add_round_robin_archive(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:1']) == 0
        # Test if RRA exists
        # Add data to rra
        for i in range(3):
            assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:1']) == 0
            time.sleep(1)
        # Fetch data and test if only last data sample exists
        info, data_src, data = rrd.fetch(self.test_db, 'LAST')
        non_empty = 0
        for d in data:
            if d[0] is not None:
                non_empty += 1
        assert non_empty == 1

        # Add RRA
        db = Database(self.test_db)
        db.add_rrd_archive(RRA('LAST', '0.5', '1', '10'))

        # Test if RRA exists
        # Add data to rra
        for i in range(3):
            assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:1']) == 0
            time.sleep(1)
        # Fetch data and test if enough data sample exists
        info, data_src, data = rrd.fetch(self.test_db, 'LAST')
        non_empty = 0
        for d in data:
            if d[0] is not None:
                non_empty += 1
        self.assertGreater(non_empty, 1)

    def test_remove_round_robin_archive(self):
        assert subprocess.call(['rrdtool', 'create', self.test_db, '--step', '1',
                                'DS:em1:GAUGE:10:U:U', 'RRA:LAST:0.5:1:1', 'RRA:LAST:0.5:1:3']) == 0
        # Test if RRA exists
        # Add data to rra
        for i in range(3):
            assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:1']) == 0
            time.sleep(1)
        # Fetch data and test if enough data sample exists
        info, data_src, data = rrd.fetch(self.test_db, 'LAST')
        non_empty = 0
        for d in data:
            if d[0] is not None:
                non_empty += 1
        assert non_empty > 1

        # Remove RRA
        db = Database(self.test_db)
        db.remove_rrd_archive(1)

        # Test if RRA was removed
        # Add data to rra
        for i in range(3):
            assert subprocess.call(['rrdtool', 'update', self.test_db, 'N:1']) == 0
            time.sleep(1)
        # Fetch data and test if enough data sample exists
        info, data_src, data = rrd.fetch(self.test_db, 'LAST')
        non_empty = 0
        for d in data:
            if d[0] is not None:
                non_empty += 1
        self.assertEqual(non_empty, 1)

    def test_parse_result(self):
        # TODO
        pass


    # TODO test database consolidate feature
    # (add data until an archive with e.g. 'AVERAGE' is filled and check wether it's filled)

# TODO test datasource/RoundRobinArchive class
# TODO test invalid/missing parameters

if __name__ == '__main__':
    unittest.main()
