"""
Tests for the influx implementation of the
electric-meter-visualizer.consumption_data_store.spi module
"""
# pylint: disable=too-many-public-methods
# pylint: disable=R0801
import uuid
from uuid import UUID
import unittest
import unittest.mock
from unittest.mock import Mock, patch
import datetime
from dateutil.tz import tzutc
from influxdb_client import Point, QueryApi
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
    DeleteRequest,
    MeasuredDatapoint,
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
        self.organisation: str = "test_organisation"

        self.now = datetime.datetime(2022, 10, 20)
        with unittest.mock.patch(
            "electric_meter_visualizer.consumption_data_store.influx.datetime",
            wraps=datetime.datetime,
        ) as mock_date:
            mock_date.now = Mock(return_value=self.now)
            self.query_builder: influx.InfluxQueryBuilder = influx.InfluxQueryBuilder(
                self.query_api,
                self.organisation,
                self.default_bucket,
            )

    def test_filter_no_bucket(self):
        """Test if no filter bucket list defaults to the default bucket"""
        self.assertEqual(self.query_builder._buckets, {self.default_bucket})

    def test_filter_empty_bucket_list(self):
        """Test if an empty bucket filter list defaults to the default bucket"""
        self.query_builder.filter_bucket(set())

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
        self.query_builder.filter_aggregate_function(set())

        self.assertEqual(self.query_builder._aggregate_function_filters, "")

    def test_filter_aggregate_function(self):
        """Test if aggregate filter contains aggregate function"""
        self.query_builder.filter_aggregate_function({AggregateFunction.SUM})

        self.assertEqual(
            self.query_builder._aggregate_function_filters,
            '|> filter(fn: (r) => r.aggregate_function == "SUM")',
        )

    def test_filter_multiple_aggregate_functions(self):
        """Test if the aggregate filter string is correct with multiple aggregate functions"""
        self.query_builder.filter_aggregate_function(
            {AggregateFunction.SUM, AggregateFunction.MAX}
        )

        filter_string: str = _normalize_text(
            self.query_builder._aggregate_function_filters
        )

        # set is unordered so both filters could be constructed
        self.assertTrue(
            filter_string
            == _normalize_text(
                '|> filter(fn: (r) => r.aggregate_function == "SUM" or \
                 r.aggregate_function == "MAX")'
            )
            or filter_string
            == _normalize_text(
                '|> filter(fn: (r) => r.aggregate_function == "MAX" or \
                 r.aggregate_function == "SUM")'
            )
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
        self.query_builder.filter_source({first_source_id, second_source_id})

        filter_string: str = _normalize_text(self.query_builder._source_filters)

        # set is unordered so both filters could be constructed
        self.assertTrue(
            filter_string
            == _normalize_text(
                f'|> filter(fn: (r) => r._measurement == "{first_source_id}" or\
                 r._measurement == "{second_source_id}")'
            )
            or filter_string
            == _normalize_text(
                f'|> filter(fn: (r) => r._measurement == "{second_source_id}" or\
                 r._measurement == "{first_source_id}")'
            )
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

            raw_0 = data_0
                    |> map(fn: (r) => ({{r with _value: float(v: r._value)}})) |> set(key: "_field", value: "raw")

            |> pivot(rowKey: ["_time",
                                "_measurement",
                                "aggregate_function"],
                                columnKey: ["_field"],
                                valueColumn: "_value")
            |> yield()
            """

        query = self.query_builder.build(datetime.timedelta(days=1), set())
        self._assert_build(
            query,
            query_mock,
            [expected_query],
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

            raw_0 = data_0
                    |> map(fn: (r) => ({{r with _value: float(v: r._value)}})) |> set(key: "_field", value: "raw")

                    |> pivot(rowKey: ["_time",
                                        "_measurement",
                                        "aggregate_function"],
                                        columnKey: ["_field"],
                                        valueColumn: "_value")
                    |> yield()
            """

        query: Query = self.query_builder.build(
            datetime.timedelta(days=1), {AggregateFunction.RAW}
        )
        self._assert_build(
            query,
            query_mock,
            [expected_query],
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
                       |> pivot(rowKey: ["_time",
                                         "_measurement",
                                         "aggregate_function"],
                                         columnKey: ["_field"],
                                         valueColumn: "_value")
                       |> yield()
            """

        query = self.query_builder.build(
            datetime.timedelta(days=1), {AggregateFunction.SUM}
        )
        self._assert_build(
            query,
            query_mock,
            [expected_query],
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
        expected_query_1: str = f"""
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
                |> pivot(rowKey: ["_time", "_measurement", "aggregate_function"], columnKey: ["_field"], valueColumn: "_value")
                |> yield()
            """

        expected_query_2: str = f"""
            {CUSTOM_AGGREGATE_FUNCTION_TEXT}

            data_0 = from(bucket: _bucket_0)
                    |> range(start: _start_date, stop: _stop_date)

            median_0 = data_0 |> {CUSTOM_AGGREGATE_NAME}(every: _aggregate_window, fn: median)
                       |> map(fn: (r) => ({{r with _value: float(v: r._value)}}))
                       |> set(key: "_field", value: "median")

            sum_0 = data_0 |> {CUSTOM_AGGREGATE_NAME}(every: _aggregate_window, fn: sum)
                       |> map(fn: (r) => ({{r with _value: float(v: r._value)}}))
                       |> set(key: "_field", value: "sum")

            union(tables: [median_0,sum_0])
                |> pivot(rowKey: ["_time", "_measurement", "aggregate_function"], columnKey: ["_field"], valueColumn: "_value")
                |> yield()
            """

        query = self.query_builder.build(
            datetime.timedelta(days=1),
            {AggregateFunction.SUM, AggregateFunction.MEDIAN},
        )
        self._assert_build(
            query,
            query_mock,
            [expected_query_1, expected_query_2],
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
        possible_queries: list[str],
        query_params: dict[str, object],
    ):
        """Assert if `QueryBuilder.build` function works correct

        Args:
            query (Query): The returned query of `QueryBuilder.build`
            query_mock (Mock): The InfluxQuery Mock object
            expected_query (str): The expected query string from the `QueryBuilder.build` `Query`
        """
        allowed_queries: list[str] = list(map(_normalize_text, possible_queries))

        query_mock.assert_called_once()
        self.assertEqual(
            query_mock.call_args[0][0], self.query_api
        )  # QueryApi parameter
        # Remove tabs and newlines for easier comparison
        # as they don't affect the query
        normalized_query_argument = _normalize_text(
            query_mock.call_args[0][1]
        )  # query string
        self.assertIn(normalized_query_argument, allowed_queries)
        self.assertEqual(query_mock.call_args[0][2], query_params)  # query parameter
        self.assertEqual(query_mock.call_args[0][3], self.organisation)  # organisation
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
                label="_measurement",
                data_type="string",
                group=False,
                default_value="",
            ),
            FluxColumn(
                3,
                label="_time",
                data_type="dateTime:RFC3339",
                group=False,
                default_value="",
            ),
            FluxColumn(
                4,
                label="_aggregate_window",
                data_type="string",
                group=False,
                default_value="",
            ),
            FluxColumn(
                5, label="min", data_type="double", group=False, default_value=""
            ),
            FluxColumn(
                6, label="mean", data_type="double", group=False, default_value=""
            ),
            FluxColumn(
                7, label="median", data_type="double", group=False, default_value=""
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
                    "_measurement": str(self.em_id),
                    "_time": self.dates[i],
                    "aggregate_function": AggregateFunction.RAW,
                    "min": self.consumption[i][0],
                    "mean": self.consumption[i][1],
                    "median": self.consumption[i][2],
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
        query_string = "query string that is irrelevant for this test"
        organisation = "test_organisation"
        query_parameter = {}

        query: Query = influx.InfluxQuery(
            self.query_api,
            query_string,
            query_parameter,
            organisation,
        )
        result: list[Datapoint] = query.execute()

        self.query_api.query.assert_called_once_with(
            query_string, organisation, query_parameter
        )

        # Result contains extra datapoint for each AggregateFunction => 3x
        self.assertEqual(len(result), 3 * len(self.consumption))

        # Filter result datapoints based on their AggregateFunction
        aggregate_min_results: list[Datapoint] = [
            datapoint
            for datapoint in result
            if datapoint.aggregate_function == AggregateFunction.MIN
        ]
        aggregate_avg_results: list[Datapoint] = [
            datapoint
            for datapoint in result
            if datapoint.aggregate_function == AggregateFunction.AVERAGE
        ]
        aggregate_med_results: list[Datapoint] = [
            datapoint
            for datapoint in result
            if datapoint.aggregate_function == AggregateFunction.MEDIAN
        ]

        # This tests if the AggregateFunctions are set correctly
        self.assertEqual(len(aggregate_min_results), len(self.consumption))
        self.assertEqual(len(aggregate_avg_results), len(self.consumption))
        self.assertEqual(len(aggregate_med_results), len(self.consumption))

        # Test if value, source and timestamp is set correctly
        for i, grouped_result in enumerate(
            (aggregate_min_results, aggregate_avg_results, aggregate_med_results)
        ):
            for j, datapoint in enumerate(grouped_result):
                with self.subTest(datapoint=datapoint):
                    self.assertEqual(datapoint.value, self.consumption[j][i])
                    self.assertEqual(datapoint.source, self.em_id)
                    self.assertEqual(datapoint.timestamp, self.dates[j])


class ConsumptionDataStoreTest(unittest.TestCase):
    """Test the influx ConsumptionDataStore implementation"""

    # pylint: disable=protected-access

    def setUp(self) -> None:
        self.organisation = "test_organisation"
        self.consumption_data_store: ConsumptionDataStore = (
            influx.InfluxConsumptionDataStore("", "", self.organisation, "")
        )

    def test_execute_retention_policy(self):
        """Test if the ConsumptionDataStore executes added RetentionPolicies"""
        retention_policy = Mock()
        self.consumption_data_store.add_retention_policy(retention_policy)

        retention_policy.execute.assert_not_called()
        self.consumption_data_store.execute_retention_policy()
        retention_policy.execute.assert_called_once()

    def test_create_query(self):
        """Test if the ConsumptionDataStore returns a QueryBuilder"""
        query_builder: QueryBuilder = self.consumption_data_store.create_query()
        self.assertIsNotNone(query_builder)

    @patch("influxdb_client.client.write_api.WriteApi.write")
    def test_put_data(self, write_api):
        """Test if the given Datapoint is properly convertet into a influx_client.Point
        and the data is written to the database
        """
        source = uuid.uuid4()
        timestamp = datetime.datetime.now()
        value = 42
        data_point: Datapoint = MeasuredDatapoint(source, value, timestamp)
        bucket = "test_bucket"

        self.consumption_data_store.put_data(data_point, bucket)

        # Assert if write was called and Point was constructed the correct way
        write_api.assert_called_once()
        self.assertEqual(write_api.call_args.args[0], bucket)
        self.assertEqual(write_api.call_args.args[1], self.organisation)
        # Assert written datapoint
        point = write_api.call_args.args[2]

        expected_point = (
            Point(source)
            .time(timestamp)
            .field("consumption", value)
            .tag("aggregate_function", AggregateFunction.RAW.name)
        )
        self.assertEqual(point._name, expected_point._name)
        self.assertEqual(point._time, expected_point._time)
        self.assertEqual(point._fields, expected_point._fields)
        self.assertEqual(point._tags, expected_point._tags)

    @patch("influxdb_client.DeleteApi.delete")
    def test_delete_data(self, delete_api):
        """Test data deletion without filters"""
        bucket = "test_bucket"
        start_date = datetime.datetime(2022, 1, 1)
        stop_date = datetime.datetime(2022, 6, 1)

        delete_request: DeleteRequest = DeleteRequest(bucket, start_date, stop_date)
        self.consumption_data_store.delete_data(delete_request)

        # Assert
        delete_api.assert_called_once_with(
            start_date, stop_date, "", bucket, self.organisation
        )

    @patch("influxdb_client.DeleteApi.delete")
    def test_delete_data_source(self, delete_api):
        """Test data deletion with source filter"""
        bucket = "test_bucket"
        start_date = datetime.datetime(2022, 1, 1)
        stop_date = datetime.datetime(2022, 6, 1)
        source = uuid.uuid4()

        delete_request: DeleteRequest = DeleteRequest(bucket, start_date, stop_date)
        delete_request.source = source

        self.consumption_data_store.delete_data(delete_request)

        # Assert
        delete_api.assert_called_once_with(
            start_date, stop_date, f'_measurement="{source}"', bucket, self.organisation
        )

    @patch("influxdb_client.DeleteApi.delete")
    def test_delete_data_aggregate_function(self, delete_api):
        """Test data deletion with aggregate_function filter"""
        bucket = "test_bucket"
        start_date = datetime.datetime(2022, 1, 1)
        stop_date = datetime.datetime(2022, 6, 1)
        aggregate_function = AggregateFunction.AVERAGE

        delete_request: DeleteRequest = DeleteRequest(bucket, start_date, stop_date)
        delete_request.aggregate_function = aggregate_function
        self.consumption_data_store.delete_data(delete_request)

        # Assert
        delete_api.assert_called_once_with(
            start_date,
            stop_date,
            f'aggregate_function="{aggregate_function.name}"',
            bucket,
            self.organisation,
        )

    @patch("influxdb_client.DeleteApi.delete")
    def test_delete_data_source_aggregate_function(self, delete_api):
        """Test data deletion with source filter and aggregate_function filter"""
        bucket = "test_bucket"
        start_date = datetime.datetime(2022, 1, 1)
        stop_date = datetime.datetime(2022, 6, 1)
        source = uuid.uuid4()
        aggregate_function = AggregateFunction.RAW

        delete_request: DeleteRequest = DeleteRequest(bucket, start_date, stop_date)
        delete_request.source = source
        delete_request.aggregate_function = aggregate_function
        self.consumption_data_store.delete_data(delete_request)

        # Assert
        delete_api.assert_called_once()
        self.assertEqual(delete_api.call_args.args[0], start_date)
        self.assertEqual(delete_api.call_args.args[1], stop_date)
        self.assertIn(
            delete_api.call_args.args[2],
            [
                f'aggregate_function="{aggregate_function.name}" AND _measurement="{source}"',
                f'_measurement="{source}" AND aggregate_function="{aggregate_function.name}"',
            ],
        )
        self.assertEqual(delete_api.call_args.args[3], bucket)
        self.assertEqual(delete_api.call_args.args[4], self.organisation)


if __name__ == "__main__":
    unittest.main()
