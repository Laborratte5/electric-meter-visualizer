"""
Tests for the influx implementation of the
electric-meter-visualizer.consumption_data_store.spi module
"""
import unittest
from electric_meter_visualizer.consumption_data_store.spi import (
    ConsumptionDataStoreFactory,
    ConsumptionDataStore,
)
from electric_meter_visualizer.consumption_data_store import influx


class ConsumptionDataStoreFactoryTest(unittest.TestCase):
    """
    Test the influx ConsumptionDataStoreFactory implementation
    """

    def setUp(self) -> None:
        self.factory: ConsumptionDataStoreFactory = (
            influx.InfluxConsumptionDataStoreFactory()
        )

    def test_consumption_data_store_not_none(self):
        """
        Test if the created ConsumptionDataStore from the factory is not None
        """
        data_store: ConsumptionDataStore = self.factory.create()
        self.assertIsNotNone(data_store)


if __name__ == "__main__":
    unittest.main()
