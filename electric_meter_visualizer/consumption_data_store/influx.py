"""This module is a concrete implementation of the spi module based on InfluxDB
"""
# pylint: disable=fixme
from uuid import UUID
from datetime import datetime
from datetime import timedelta
import logging
from influxdb_client.client import flux_table
import influxdb_client.client.query_api as influx_query_api
from electric_meter_visualizer.consumption_data_store import spi

logger = logging.getLogger(__name__)

AGGREGATE_MAPPING: dict[spi.AggregateFunction, str] = {
    spi.AggregateFunction.SUM: "sum",
    spi.AggregateFunction.AVERAGE: "mean",
    spi.AggregateFunction.MEDIAN: "median",
    spi.AggregateFunction.MIN: "min",
    spi.AggregateFunction.MAX: "max",
    spi.AggregateFunction.QUANTILE: "quantile",
}

REVERSE_AGGREGATE_MAPPING: dict[str, spi.AggregateFunction] = {
    name: function for function, name in AGGREGATE_MAPPING.items()
}


class InfluxQuery(spi.Query):
    """
    Representation of a Flux query
    """

    def __init__(
        self,
        query_api: influx_query_api.QueryApi,
        query: str,
        query_parameter: dict[str, object],
    ):
        """Create a new Query for an InfluxConsumptionDataStore"""
        self.query_api: influx_query_api.QueryApi = query_api
        self.query: str = query
        self.query_parameter: dict[str, object] = query_parameter

    def execute(self) -> list[spi.Datapoint]:
        """Execute this query

        Returns:
            list[spi.Datapoint]: parsed query result
        """
        result: flux_table.TableList = self.query_api.query(
            self.query, self.query_parameter
        )
        datapoints: list[spi.Datapoint] = []

        for table in result:
            for record in table.records:
                datapoint: spi.Datapoint = spi.Datapoint(
                    record["energy_meter_id"],  # datapoint.source
                    record["_start"],  # datapoint.start
                    record["_stop"],  # datapoint.stop
                    # Each key in record.values that is also a key of REVERSE_AGGREGATE_MAPPING
                    # is the result of an AggregateFunction.
                    # For each of these keys create a AggregateFunction->value mapping
                    {
                        REVERSE_AGGREGATE_MAPPING[name]: value
                        for name, value in record.values.items()
                        if name in REVERSE_AGGREGATE_MAPPING
                    },  # datapoint.value
                )

                datapoints.append(datapoint)

        return datapoints

    def __hash__(self):
        # TODO implement
        pass


class InfluxQueryBuilder(spi.QueryBuilder):
    """
    Helper class to build InfluxQuery objects
    """

    def __init__(self, query_api: influx_query_api.QueryApi, default_bucket: str):
        self.query_api: influx_query_api.QueryApi = query_api
        self._default_bucket: str = default_bucket
        self._buckets: set[str] = {default_bucket}
        self._source_filters: str = ""
        self._start_date: object = timedelta(days=0)
        self._stop_date: object = datetime.now()

    def filter_bucket(self, bucket_list: set[str]) -> spi.QueryBuilder:
        self._buckets = bucket_list
        if not bucket_list:
            self._buckets = {self._default_bucket}

        return self

    def filter_source(self, id_list: set[UUID]) -> spi.QueryBuilder:
        condition: str = " or ".join(
            f'r.energy_meter_id == "{meter_id}"' for meter_id in id_list
        )

        if condition:
            self._source_filters = f"|> filter(fn: (r) => {condition})"

        logger.debug("Query Filter: '%s'", self._source_filters)
        return self

    def filter_start(self, start_date: datetime) -> spi.QueryBuilder:
        self._start_date = start_date
        return self

    def filter_stop(self, stop_date: datetime) -> spi.QueryBuilder:
        self._stop_date = stop_date
        return self

    def build(
        self,
        aggregate_window: timedelta,
        aggregate_functions: set[spi.AggregateFunction],
    ) -> spi.Query:
        if (
            spi.AggregateFunction.RAW in aggregate_functions
            and len(aggregate_functions) > 1
        ):
            raise ValueError(
                "AggregateFunction.RAW cannot be used in conjunction with other AggregateFunctions"
            )

        if len(aggregate_functions) == 0:
            aggregate_functions = {spi.AggregateFunction.RAW}

        data_query: str = ""
        aggregate_query: str = ""
        bucket_names: dict[str, str] = {}
        aggregate_function_data: list[str] = []
        for i, bucket in enumerate(self._buckets):
            # Build data query
            data_query = (
                data_query
                + f"""
                data_{i} = from(bucket: _bucket_{i})
                    |> range(start: _start_date, stop: _stop_date)
                    |> filter(fn: (r) => r._measurement == "energy_consumption")
                    {self._source_filters}
            """
            )
            bucket_names[f"_bucket_{i}"] = bucket

            # Build aggregate functions
            if spi.AggregateFunction.RAW not in aggregate_functions:
                aggregate_function_names: list[str] = [
                    AGGREGATE_MAPPING[aggregate_function]
                    for aggregate_function in aggregate_functions
                ]
                for aggregate_function_name in aggregate_function_names:
                    aggregate_query = (
                        aggregate_query
                        + f"""
                        {aggregate_function_name}_{i} = data_{i} |> customAggregateWindow(every: _aggregate_window, fn: {aggregate_function_name})
                            |> map(fn: (r) => ({{r with _value: float(v: r._value)}})) |> set(key: "_field", value: "{aggregate_function_name}")
                    """
                    )

                    # Aggregate data list
                    aggregate_function_data.append(f"{aggregate_function_name}_{i}")

        # Build union
        union = (
            f"""
            union(tables: [{",".join(aggregate_function_data)}])
            |> pivot(rowKey: ["_start",
                              "_stop",
                              "energy_meter_id"],
                              columnKey: ["_field"],
                              valueColumn: "_value")
            |> yield()
            """
            if len(aggregate_functions) > 1
            else "|> yield()"
        )

        logger.debug("Union: %s", union)

        # Build Query
        query: str = f"""
            customAggregateWindow = (every, fn, column="_value", timeSrc="_stop", timeDst="_time", tables=<-) =>
                tables
                    |> window(every: every)
                    |> fn()
                    |> duplicate(column: timeSrc, as: timeDst)
                    |> group()

            {data_query}

            {aggregate_query}
            {union}
        """

        query_parameters: dict[str, object] = {
            **bucket_names,
            "_start_date": self._start_date,
            "_stop_date": self._stop_date,
        }
        if spi.AggregateFunction.RAW not in aggregate_functions:
            query_parameters["_aggregate_window"] = aggregate_window

        return InfluxQuery(self.query_api, query, query_parameters)


class InfluxConsumptionDataStore(spi.ConsumptionDataStore):
    """
    This class implements the ConsumptionDataStore backed by an InfluxDatabase
    """

    def create_query(self) -> spi.QueryBuilder:
        # TODO implement
        pass

    def put_data(self, datapoint: spi.Datapoint, bucket: str):
        # TODO implement
        pass

    def delete_data(self, datapoint: spi.Datapoint, bucket: str):
        # TODO implement
        pass

    def delete_bucket(self, bucket: str):
        # TODO implement
        pass


class InfluxConsumptionDataStoreFactory(
    spi.ConsumptionDataStoreFactory
):  # pylint: disable=too-few-public-methods
    """
    Helper class to create a concrete object of the InfluxConsumptionDataStore
    """

    def create(self) -> spi.ConsumptionDataStore:
        return InfluxConsumptionDataStore()
