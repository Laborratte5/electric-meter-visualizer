"""
Tests for the influx implementation of the
electric-meter-visualizer.consumption_data_store.spi module
"""
# pylint: disable=too-many-public-methods
# pylint: disable=R0801
import uuid
from uuid import UUID
import unittest
from unittest.mock import Mock, patch
import datetime
from dateutil.tz import tzutc
from influxdb_client import QueryApi
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
    QueryBuilder,
)
from electric_meter_visualizer.consumption_data_store import influx


CUSTOM_AGGREGATE_NAME: str = "customAggregateWindow"

CUSTOM_AGGREGATE_FUNCTION_TEXT: str = f"""
    {CUSTOM_AGGREGATE_NAME} = (every, fn, column="_value", timeSrc="_stop", timeDst="_time", tables=<-) =>
                    tables
                        |> window(every: every)
                        |> fn()
                        |> duplicate(column: timeSrc, as: timeDst)
                        |> group()
    """


def _normalize_text(text: str) -> str:
    """Normalize text for easier comparison

    Normalizes text by removing tabs and newlines.
    Trims multiple consecutive whitespaces to a single whitespace
    Args:
        text (str): The text that should be normalized

    Returns:
        str: the normalized text
    """
    text = text.replace("\n", "").replace("\t", "")
    prev: str = ""
    while text != prev:
        prev = text
        text = text.replace("  ", " ")

    return text


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


class QueryBuilderTest(unittest.TestCase):
    """Test the influx QueryBuilder implementation"""

    # pylint: disable=protected-access

    def setUp(self) -> None:
        self.query_api: QueryApi = Mock()
        self.default_bucket: str = "default_test_bucket"

        self.now = datetime.datetime(2022, 10, 20)
        with unittest.mock.patch(
            "electric_meter_visualizer.consumption_data_store.influx.datetime",
            wraps=datetime.datetime,
        ) as mock_date:
            mock_date.now = Mock(return_value=self.now)
            self.query_builder: QueryBuilder = influx.InfluxQueryBuilder(
                self.query_api,
                self.default_bucket,
            )

    def test_filter_no_bucket(self):
        """Test if no filter bucket list defaults to the default bucket"""
        self.assertEqual(self.query_builder._buckets, {self.default_bucket})

    def test_filter_empty_bucket_list(self):
        """Test if an empty bucket filter list defaults to the default bucket"""
        self.query_builder.filter_bucket([])

        self.assertEqual(self.query_builder._buckets, {self.default_bucket})

    def test_filter_bucket(self):
        """Test if the filter list is set"""
        self.query_builder.filter_bucket({"test_bucket_1"})

        self.assertEqual(self.query_builder._buckets, {"test_bucket_1"})

    def test_filter_multiple_buckets(self):
        """Test if the filter list with multiple buckets is set"""
        self.query_builder.filter_bucket({"test_bucket_1", "test_bucket_2"})

        self.assertEqual(
            self.query_builder._buckets, {"test_bucket_1", "test_bucket_2"}
        )

    def test_filter_no_aggregate_function_list(self):
        """Test if no aggregate function list defaults to no filter"""
        self.assertEqual(self.query_builder._aggregate_function_filters, "")

    def test_filter_empty_aggregate_function_list(self):
        """Test if empty aggregate function list defaults to no filter"""
        self.query_builder.filter_aggregate_function([])

        self.assertEqual(self.query_builder._aggregate_function_filters, "")

    def test_filter_aggregate_function(self):
        """Test if aggregate filter contains aggregate function"""
        self.query_builder.filter_aggregate_function([AggregateFunction.SUM])

        self.assertEqual(
            self.query_builder._aggregate_function_filters,
            '|> filter(fn: (r) => r.aggregate_function == "SUM")',
        )

    def test_filter_multiple_aggregate_functions(self):
        """Test if the aggregate filter string is correct with multiple aggregate functions"""
        self.query_builder.filter_aggregate_function(
            [AggregateFunction.SUM, AggregateFunction.MAX]
        )

        self.assertEqual(
            _normalize_text(self.query_builder._aggregate_function_filters),
            _normalize_text(
                '|> filter(fn: (r) => r.aggregate_function == "SUM" or \
                 r.aggregate_function == "MAX")'
            ),
        )

    def test_filter_no_source(self):
        """Test if source filter string is empty"""
        self.assertEqual(self.query_builder._source_filters, "")

    def test_filter_source(self):
        """Test if source filter contains source id"""
        source_id: UUID = uuid.uuid4()
        self.query_builder.filter_source({source_id})

        self.assertEqual(
            self.query_builder._source_filters,
            f'|> filter(fn: (r) => r._measurement == "{source_id}")',
        )

    def test_filter_multiple_sources(self):
        """Test if the source filter string is correct with multiple sources"""
        first_source_id: UUID = uuid.uuid4()
        second_source_id: UUID = uuid.uuid4()
        self.query_builder.filter_source([first_source_id, second_source_id])

        self.assertEqual(
            _normalize_text(self.query_builder._source_filters),
            _normalize_text(
                f'|> filter(fn: (r) => r._measurement == "{first_source_id}" or\
                 r._measurement == "{second_source_id}")'
            ),
        )

    def test_filter_no_start(self):
        """Test if the default value for start_date is 0d"""
        self.assertEqual(self.query_builder._start_date, datetime.timedelta(days=0))

    def test_filter_start(self):
        """Test that the start date is correct"""
        start_date: datetime.datetime = datetime.datetime(2022, 10, 10)
        self.query_builder.filter_start(start_date)

        self.assertEqual(self.query_builder._start_date, start_date)

    def test_filter_multiple_start_calls(self):
        """Test that the start date is correct after multiple calls"""
        start_date: datetime.datetime = datetime.datetime(2022, 10, 10)
        self.query_builder.filter_start(datetime.datetime(2000, 12, 31))
        self.query_builder.filter_start(start_date)

        self.assertEqual(self.query_builder._start_date, start_date)

    def test_filter_no_stop(self):
        """Test if the default value for stop_date is `now()`"""
        self.assertEqual(self.query_builder._stop_date, self.now)

    def test_filter_stop(self):
        """Test that the stop date is correct"""
        stop_date: datetime.datetime = datetime.datetime(2022, 10, 10)
        self.query_builder.filter_stop(stop_date)

        self.assertEqual(self.query_builder._stop_date, stop_date)

    def test_filter_multiple_stop_calls(self):
        """Test that the stop date is correct after multiple calls"""
        stop_date: datetime.datetime = datetime.datetime(2022, 10, 10)
        self.query_builder.filter_stop(datetime.datetime(2000, 12, 31))
        self.query_builder.filter_stop(stop_date)

        self.assertEqual(self.query_builder._stop_date, stop_date)

    def test_build_aggregate_raw_with_other(self):
        """Test if a ValueError is raised if AggregateFunction.RAW
        is used in conjunction with another AggregateFunction"""
        self.assertRaises(
            ValueError,
            self.query_builder.build,
            datetime.timedelta(days=1),
            [AggregateFunction.RAW, AggregateFunction.SUM],
        )

    @patch("electric_meter_visualizer.consumption_data_store.influx.InfluxQuery")
    def test_build_no_aggregate_functions(self, query_mock):
        """Test if no supplied aggregate function defaults to `AggregateFunction.RAW`"""
        expected_query: str = f"""
            {CUSTOM_AGGREGATE_FUNCTION_TEXT}

            data_0 = from(bucket: _bucket_0)
                    |> range(start: _start_date, stop: _stop_date)
                    |> yield()
            """

        query = self.query_builder.build(datetime.timedelta(days=1), [])
        self._assert_build(
            query,
            query_mock,
            expected_query,
            {
                "_bucket_0": self.default_bucket,
                "_start_date": datetime.timedelta(days=0),
                "_stop_date": self.now,
            },
        )

    @patch("electric_meter_visualizer.consumption_data_store.influx.InfluxQuery")
    def test_build_aggregate_raw(self, query_mock):
        """Test if query for `AggregateFunction.RAW` is correct"""
        expected_query: str = f"""
            {CUSTOM_AGGREGATE_FUNCTION_TEXT}

            data_0 = from(bucket: _bucket_0)
                    |> range(start: _start_date, stop: _stop_date)
                    |> yield()
            """

        query: Query = self.query_builder.build(
            datetime.timedelta(days=1), [AggregateFunction.RAW]
        )
        self._assert_build(
            query,
            query_mock,
            expected_query,
            {
                "_bucket_0": self.default_bucket,
                "_start_date": datetime.timedelta(days=0),
                "_stop_date": self.now,
            },
        )

    @patch("electric_meter_visualizer.consumption_data_store.influx.InfluxQuery")
    def test_build_aggregate_function(self, query_mock):
        """Test if Query for `AggregateFunction.SUM` is correct"""
        expected_query: str = f"""
            {CUSTOM_AGGREGATE_FUNCTION_TEXT}

            data_0 = from(bucket: _bucket_0)
                    |> range(start: _start_date, stop: _stop_date)

            sum_0 = data_0 |> {CUSTOM_AGGREGATE_NAME}(every: _aggregate_window, fn: sum)
                       |> map(fn: (r) => ({{r with _value: float(v: r._value)}}))
                       |> set(key: "_field", value: "sum")
                       |> yield()
            """

        query = self.query_builder.build(
            datetime.timedelta(days=1), [AggregateFunction.SUM]
        )
        self._assert_build(
            query,
            query_mock,
            expected_query,
            {
                "_bucket_0": self.default_bucket,
                "_start_date": datetime.timedelta(days=0),
                "_stop_date": self.now,
                "_aggregate_window": datetime.timedelta(days=1),
            },
        )

    @patch("electric_meter_visualizer.consumption_data_store.influx.InfluxQuery")
    def test_build_multiple_aggregate_functions(self, query_mock):
        """Test if Query for `AggregateFunction.SUM` and `AggregateFunction.MAX` is correct"""
        expected_query: str = f"""
            {CUSTOM_AGGREGATE_FUNCTION_TEXT}

            data_0 = from(bucket: _bucket_0)
                    |> range(start: _start_date, stop: _stop_date)

            sum_0 = data_0 |> {CUSTOM_AGGREGATE_NAME}(every: _aggregate_window, fn: sum)
                       |> map(fn: (r) => ({{r with _value: float(v: r._value)}}))
                       |> set(key: "_field", value: "sum")

            median_0 = data_0 |> {CUSTOM_AGGREGATE_NAME}(every: _aggregate_window, fn: median)
                       |> map(fn: (r) => ({{r with _value: float(v: r._value)}}))
                       |> set(key: "_field", value: "median")

            union(tables: [sum_0,median_0])
                |> pivot(rowKey: ["_start", "_stop", "energy_meter_id"], columnKey: ["_field"], valueColumn: "_value")
                |> yield()
            """

        query = self.query_builder.build(
            datetime.timedelta(days=1),
            [AggregateFunction.SUM, AggregateFunction.MEDIAN],
        )
        self._assert_build(
            query,
            query_mock,
            expected_query,
            {
                "_bucket_0": self.default_bucket,
                "_start_date": datetime.timedelta(days=0),
                "_stop_date": self.now,
                "_aggregate_window": datetime.timedelta(days=1),
            },
        )

    def _assert_build(
        self,
        query: Query,
        query_mock,
        expected_query: str,
        query_params: dict[str, object],
    ):
        """Assert if `QueryBuilder.build` function works correct

        Args:
            query (Query): The returned query of `QueryBuilder.build`
            query_mock (Mock): The InfluxQuery Mock object
            expected_query (str): The expected query string from the `QueryBuilder.build` `Query`
        """
        expected_query = _normalize_text(expected_query)

        query_mock.assert_called_once()
        self.assertEqual(
            query_mock.call_args[0][0], self.query_api
        )  # QueryApi parameter
        # Remove tabs and newlines for easier comparison
        # as they don't affect the query
        normalized_query_argument = _normalize_text(
            query_mock.call_args[0][1]
        )  # query string
        self.assertEqual(normalized_query_argument, expected_query)
        self.assertEqual(query_mock.call_args[0][2], query_params)  # query parameter
        self.assertIsNotNone(query)


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
                    "energy_meter_id": self.em_id,
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
            self.assertIn(datapoint.start, self.dates)
            self.assertIn(datapoint.stop, self.dates)
            self.assertIn(AggregateFunction.MIN, datapoint.value.keys())
            self.assertIn(AggregateFunction.AVERAGE, datapoint.value.keys())
            self.assertIn(AggregateFunction.MEDIAN, datapoint.value.keys())
            self.assertEqual(
                datapoint.value[AggregateFunction.MIN], self.consumption[i][0]
            )
            self.assertEqual(
                datapoint.value[AggregateFunction.AVERAGE], self.consumption[i][1]
            )
            self.assertEqual(
                datapoint.value[AggregateFunction.MEDIAN], self.consumption[i][2]
            )


if __name__ == "__main__":
    unittest.main()
