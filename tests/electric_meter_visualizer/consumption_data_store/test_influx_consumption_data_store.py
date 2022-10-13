"""
Tests for the influx implementation of the
electric-meter-visualizer.consumption_data_store.spi module
"""
import uuid
from uuid import UUID
import unittest
from unittest.mock import Mock
import datetime
from dateutil.tz import tzutc
from influxdb_client.client.flux_table import (
    FluxColumn,
    FluxTable,
    FluxRecord,
)
from electric_meter_visualizer.consumption_data_store.spi import (
    AggregateFunction,
    ConsumptionDataStoreFactory,
    ConsumptionDataStore,
    Datapoint,
    Query,
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


class QueryTest(unittest.TestCase):
    """
    Test the influx Query implementation
    """

    def setUp(self) -> None:
        table: FluxTable = FluxTable()
        # Columns
        table.columns = [
            FluxColumn(
                0,
                label="result",
                data_type="string",
                group=False,
                default_value="_result",
            ),
            FluxColumn(
                1, label="table", data_type="long", group=False, default_value=""
            ),
            FluxColumn(
                2,
                label="_start",
                data_type="dateTime:RFC3339",
                group=False,
                default_value="",
            ),
            FluxColumn(
                3,
                label="_stop",
                data_type="dateTime:RFC3339",
                group=False,
                default_value="",
            ),
            FluxColumn(
                4, label="min", data_type="double", group=False, default_value=""
            ),
            FluxColumn(
                5, label="mean", data_type="double", group=False, default_value=""
            ),
            FluxColumn(
                6, label="median", data_type="double", group=False, default_value=""
            ),
        ]
        # Records
        self.dates = (
            datetime.datetime(2022, 10, 1, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 2, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 3, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 4, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 5, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 6, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 7, 0, 0, tzinfo=tzutc()),
            datetime.datetime(2022, 10, 8, 0, 0, tzinfo=tzutc()),
        )
        self.consumption = (
            # (min, mean, median)
            (3.0, 7.3, 6.0),
            (1.0, 5.3, 6.0),
            (5.0, 6.3, 3.0),
            (7.0, 13.3, 8.0),
            (4.0, 4.3, 4.5),
            (2.0, 4.3, 5.5),
            (2.0, 3.3, 3.0),
        )
        self.em_id: UUID = uuid.uuid4()
        table.records = [
            FluxRecord(
                0,
                values={
                    "result": "_result",
                    "table": 0,
                    "_start": self.dates[i],
                    "_stop": self.dates[i + 1],
                    "min": self.consumption[i][0],
                    "mean": self.consumption[i][1],
                    "median": self.consumption[i][2],
                    "em": self.em_id,
                },
            )
            for i in range(7)
        ]

        table_list: list[FluxTable] = [
            table,
        ]

        self.bucket_name = "test_bucket"

        self.query_api = Mock()
        self.query_api.query.return_value = table_list

    def test_query_parse_result(self):
        """
        Test if the Query correctly parses the output of the influx database
        to a list of Datapoints
        """
        query: Query = influx.InfluxQuery(
            self.query_api,
            "query string that is irrelevant for this test",
            {},
        )
        result: list[Datapoint] = query.execute()

        self.query_api.query.assert_called()
        self.assertEqual(len(result), len(self.consumption))
        for i, datapoint in enumerate(result):
            self.assertEqual(datapoint.source, self.em_id)
            self.assertEqual(datapoint.bucket, self.bucket_name)
            self.assertIn(datapoint.start, self.dates)
            self.assertIn(datapoint.stop, self.dates)
            self.assertIn(AggregateFunction.MIN, datapoint.value.keys())
            self.assertIn(AggregateFunction.AVERAGE, datapoint.value.keys())
            self.assertIn(AggregateFunction.MEDIAN, datapoint.value.keys())
            self.assertEqual(
                datapoint.value[AggregateFunction.MIN], datapoint.value[i][0]
            )
            self.assertEqual(
                datapoint.value[AggregateFunction.AVERAGE], datapoint.value[i][1]
            )
            self.assertEqual(
                datapoint.value[AggregateFunction.MEDIAN], datapoint.value[i][2]
            )


if __name__ == "__main__":
    unittest.main()
