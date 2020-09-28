import unittest

from ElectricMeterMockup import ElectricMeterMockup
from Database import Datasource as DS
from Logic import Logic


class DatabaseMock:

    def __init__(self):
        self.data_sources = []

    def add_data(self, data_list, time='N'):
        pass

    def get_data(self, start_time=None, end_time='now'):
        pass

    def add_data_source(self, ds):
        self.data_sources.append(ds)

    def remove_data_source(self, ds):
        pass

    def add_rrd_archive(self, rra):
        pass

    def remove_rrd_archive(self, idx):
        pass


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.logic = Logic(True)
        self.db_mock = DatabaseMock()
        self.logic.database = self.db_mock

    def test_add_electric_meter(self):
        data_src_prev_len = len(self.db_mock.data_sources)
        electric_meters_prev_len = len(self.logic.electric_meters)
        self.logic.add_electric_meter(0, 0, False, 'Meter1')

        # Check if Datasource was created
        self.assertGreater(len(self.db_mock.data_sources), 0)
        self.assertGreater(len(self.logic.datasources), 0)
        # Check if Electric meter was created
        self.assertGreater(len(self.logic.electric_meter_datasource_mapping.keys()), 0)
        self.assertGreater(len(self.logic.electric_meters), 0)

    def test_remove_electric_meter(self):
        # Setup
        # Create ElectricMeter
        em1 = ElectricMeterMockup(10, 0, False, 'em1')
        em2 = ElectricMeterMockup(20, 0, False, 'em2')
        # Associate ElectricMeter with id
        self.logic.electric_meters[1] = em1
        self.logic.electric_meters[2] = em2
        # Create Datasource
        ds1 = DS('em1','GAUGE', 1800)
        ds2 = DS('em2','GAUGE', 1800)
        self.db_mock.add_data_source(ds1)
        self.db_mock.add_data_source(ds2)
        # Associate Datasource with ElectricMeter
        self.logic.electric_meter_datasource_mapping[em1] = ds1
        self.logic.electric_meter_datasource_mapping[em2] = ds2
        # Add Datasource to DatasourceList
        self.logic.datasources.append(ds1)
        self.logic.datasources.append(ds2)

        # Remove Electric Meter 2
        self.logic.remove_electric_meter(2)

        # Check if Electric Meter 2 was removed
        self.assertNotIn(em2, self.logic.electric_meters.items())
        self.assertNotIn(ds2, self.db_mock.data_sources)
        self.assertNotIn(ds2, self.logic.datasources)
        self.assertNotIn(em2, self.logic.electric_meter_datasource_mapping.keys())
        self.assertNotIn(ds2, self.logic.electric_meter_datasource_mapping.items())
        self.assertIn(em1, self.logic.electric_meters.items())
        self.assertIn(ds1, self.db_mock.data_sources)
        self.assertIn(ds1, self.logic.datasources)
        self.assertIn(em1, self.logic.electric_meter_datasource_mapping.keys())
        self.assertIn(ds1, self.logic.electric_meter_datasource_mapping.items())

    def test_remove_last_electric_meter(self):
        # Setup
        # Create ElectricMeter
        em1 = ElectricMeterMockup(10, 0, False, 'em1')
        # Associate ElectricMeter with id
        self.logic.electric_meters[1] = em1
        # Create Datasource
        ds1 = DS('em1', 'GAUGE', 1800)
        self.db_mock.add_data_source(ds1)
        # Associate Datasource with ElectricMeter
        self.logic.electric_meter_datasource_mapping[em1] = ds1
        # Add Datasource to DatasourceList
        self.logic.datasources.append(ds1)

        # Remove Electric Meter 1 but one datasource still exists
        self.logic.remove_electric_meter(1)

        # Check if Electric Meter 1 was removed
        self.assertEqual(len(self.logic.electric_meters.items()), 1)  # Dummy Electric Meter
        self.assertNotIn(em1, self.logic.electric_meters.items())
        self.assertEqual(len(self.db_mock.data_sources), 1)  # Dummy Datasource
        self.assertNotIn(ds1, self.db_mock.data_sources)
        self.assertEqual(len(self.logic.electric_meter_datasource_mapping.keys()), 1)  # Dummy ElectricMeter/Datasource
        self.assertEqual(len(self.logic.electric_meter_datasource_mapping.items()), 1)  # Dummy ElectricMeter/Datasource
        self.assertNotIn(em1, self.logic.electric_meter_datasource_mapping.keys())
        self.assertNotIn(ds1, self.logic.electric_meter_datasource_mapping.items())
        self.assertEqual(len(self.logic.datasources), 1)
        self.assertNotIn(ds1, self.logic.datasources)

    def test_get_electric_meters(self):
        # TODO write test
        # Test really necessary?
        pass

    def test_change_electric_meter(self):
        # Setup
        self.logic.add_electric_meter(10, 0, False, 'em1')

        # Change Electric Meter
        self.logic.change_electric_meter(self.logic.next_id, 100, 500, True, 'changed_em1')

        # Check if Electric Meter data was changed
        em = self.logic.get_electric_meter(self.logic.next_id)
        self.assertEqual(em.value, 100)
        self.assertEqual(em.pin, 500)
        self.assertEqual(em.active_low, True)
        self.assertEqual(em.name, 'changed_em1')


if __name__ == '__main__':
    unittest.main()
