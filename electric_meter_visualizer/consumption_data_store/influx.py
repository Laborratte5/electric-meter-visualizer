"""This module is a concrete implementation of the spi module based on InfluxDB
"""

import json
import logging
import typing
from datetime import datetime, timedelta
from uuid import UUID

import influxdb_client
import influxdb_client.client.bucket_api as influx_bucket_api
import influxdb_client.client.query_api as influx_query_api
import influxdb_client.client.tasks_api as influx_task_api
import influxdb_client.client.write_api as influx_write_api
import influxdb_client.domain as influx_domain
from influxdb_client.client import flux_table
from jinja2 import Environment, PackageLoader
from optional import Optional

from electric_meter_visualizer.consumption_data_store import spi

logger = logging.getLogger(__name__)

AGGREGATE_MAPPING: dict[spi.AggregateFunction, str] = {
    spi.AggregateFunction.SUM: "sum",
    spi.AggregateFunction.AVERAGE: "mean",
    spi.AggregateFunction.MEDIAN: "median",
    spi.AggregateFunction.MIN: "min",
    spi.AggregateFunction.MAX: "max",
    spi.AggregateFunction.QUANTILE: "quantile",
    spi.AggregateFunction.RAW: "raw",
}


class InfluxFilterBuilder(spi.FilterBuilder):
    """Builder to create simple filters in flux"""

    def __init__(self) -> None:
        """Create a new InfluxFilterBuilder instance

        Note: The InfluxFilterBuilder is only used internally
              there should be no need to create an InfluxFilterBuilder
              instance outside of the `influx.py` module
        """
        super().__init__()
        self._aggregate_function_filters: str = ""
        self._source_filters: str = ""

    def filter_aggregate_function(
        self, aggregate_function_list: set[spi.AggregateFunction]
    ):
        condition: str = " or ".join(
            f'r.aggregate_function == "{aggregate_function.name}"'
            for aggregate_function in aggregate_function_list
        )

        if condition:
            self._aggregate_function_filters = f"|> filter(fn: (r) => {condition})"

        logger.debug(
            "Aggregate Function Filter: '%s'", self._aggregate_function_filters
        )

    def filter_source(self, id_list: set[UUID]):
        condition: str = " or ".join(
            f'r._measurement == "{meter_id}"' for meter_id in id_list
        )

        if condition:
            self._source_filters = f"|> filter(fn: (r) => {condition})"

        logger.debug("Query Filter: '%s'", self._source_filters)

    def build(self) -> str:
        """Create the Influx Query filter string

        Returns:
            str: Query string representing the filters of this filter builder
        """
        return self._source_filters + self._aggregate_function_filters


class InfluxQuery(spi.Query):
    """
    Representation of a Flux query
    """

    def __init__(
        self,
        query_api: influx_query_api.QueryApi,
        query: str,
        query_parameter: dict[str, object],
        organisation: str,
    ):
        """Create a new Query for an InfluxConsumptionDataStore"""
        self.query_api: influx_query_api.QueryApi = query_api
        self.query: str = query
        self.query_parameter: dict[str, object] = query_parameter
        self.organisation: str = organisation

    def execute(self) -> list[spi.Datapoint]:
        """Execute this query

        Returns:
            list[spi.Datapoint]: parsed query result
        """
        datapoints: list[spi.Datapoint] = []

        logger.debug(self.query)
        logger.debug(self.query_parameter)

        result: flux_table.TableList = self.query_api.query(
            self.query, self.organisation, self.query_parameter
        )

        logger.debug(result)

        for table in result:
            for record in table.records:
                source: UUID = UUID(record["_measurement"])
                timestamp: datetime = record["_time"]

                for (
                    aggregate_function,
                    aggregate_function_name,
                ) in AGGREGATE_MAPPING.items():
                    if aggregate_function_name in record.values.keys():
                        datapoint: spi.Datapoint = spi.Datapoint(
                            source,
                            record[aggregate_function_name],
                            timestamp,
                            aggregate_function,
                        )

                        datapoints.append(datapoint)

        return datapoints

    def __hash__(self):
        # TODO implement
        pass


class InfluxBucket(spi.Bucket):
    """Representation of a Bucket in the Influx Database"""

    def __init__(
        self, bucket_api: influx_bucket_api.BucketsApi, bucket: influx_domain.Bucket
    ):
        super().__init__(bucket.id)
        self._bucket_api: influx_bucket_api.BucketsApi = bucket_api
        self._bucket: influx_domain.Bucket = bucket

        # Set retention period
        retention_rule_list: list[
            influx_domain.BucketRetentionRules
        ] = self._bucket.retention_rules
        if retention_rule_list:
            retetion_rule: influx_domain.BucketRetentionRules = retention_rule_list[0]
            self._retention_period = timedelta(seconds=int(retetion_rule.every_seconds))

        # TODO set existing downsample tasks with this bucket as source

    def _set_retention_period(self, retention_period: timedelta) -> None:
        every_seconds: int = int(retention_period.total_seconds())
        shard_group_duration_seconds: int = int(
            retention_period.total_seconds() / 2
        )  # TODO ggf besser berechnen bzw. anpassen

        self._bucket.retention_rules = [
            influx_domain.BucketRetentionRules(
                every_seconds=every_seconds,
                shard_group_duration_seconds=shard_group_duration_seconds,
            )
        ]
        self._bucket_api.update_bucket(self._bucket)


class InfluxQueryBuilder(spi.QueryBuilder):
    """
    Helper class to build InfluxQuery objects
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        query_api: influx_query_api.QueryApi,
        organisation: str,
        default_buckets: set[spi.Bucket],
    ):
        self.query_api: influx_query_api.QueryApi = query_api
        self._default_buckets: set[spi.Bucket] = default_buckets
        self._buckets: set[spi.Bucket] = self._default_buckets
        self._filter_builder: InfluxFilterBuilder = InfluxFilterBuilder()
        self._start_date: object = timedelta(days=0)
        self._stop_date: object = datetime.now()
        self.organisation: str = organisation

    def filter_bucket(self, bucket_list: set[spi.Bucket]) -> spi.QueryBuilder:
        self._buckets = bucket_list
        if not bucket_list:
            self._buckets = self._default_buckets

        return self

    def filter_source(self, id_list: set[UUID]) -> spi.QueryBuilder:
        self._filter_builder.filter_source(id_list)
        return self

    def filter_aggregate_function(
        self, aggregate_function_list: set[spi.AggregateFunction]
    ) -> spi.QueryBuilder:
        self._filter_builder.filter_aggregate_function(aggregate_function_list)
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
                "AggregateFunction.RAW cannot be used in conjunction \
                 with other AggregateFunctions"
            )

        if len(aggregate_functions) == 0:
            aggregate_functions = {spi.AggregateFunction.RAW}

        data_query: str = ""
        aggregate_query: str = ""
        bucket_ids: dict[str, str] = {}
        aggregate_function_data: list[str] = []
        for i, bucket in enumerate(self._buckets):
            # Build data query
            data_query = (
                data_query  # TODO Änderung auf bucketID testen
                + f"""
                data_{i} = from(bucketID: _bucket_{i})
                    |> range(start: _start_date, stop: _stop_date)
                    {self._filter_builder.build()}
            """
            )
            bucket_ids[f"_bucket_{i}"] = bucket.identifier

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
            else:
                aggregate_query = (
                    aggregate_query
                    + f"""
                        {AGGREGATE_MAPPING[spi.AggregateFunction.RAW]}_{i} = data_{i}
                            |> map(fn: (r) => ({{r with _value: float(v: r._value)}})) |> set(key: "_field", value: "{AGGREGATE_MAPPING[spi.AggregateFunction.RAW]}")
                    """
                )

        # Build union
        union = (
            f"""
            union(tables: [{",".join(aggregate_function_data)}])
            """
            if len(aggregate_functions) > 1
            else ""
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
            |> pivot(rowKey: ["_time",
                    "_measurement",
                    "aggregate_function"],
                    columnKey: ["_field"],
                    valueColumn: "_value")
            |> yield()
        """

        query_parameters: dict[str, object] = {
            **bucket_ids,
            "_start_date": self._start_date,
            "_stop_date": self._stop_date,
        }
        if spi.AggregateFunction.RAW not in aggregate_functions:
            query_parameters["_aggregate_window"] = aggregate_window

        return InfluxQuery(self.query_api, query, query_parameters, self.organisation)


class DownsampleTaskMapper:
    """Class to manage mapping between downsample
    task id and downsample task information"""

    def __init__(self, file_path: str) -> None:
        self._file_path: str = file_path
        self._not_installed_tasks: list[dict[str, typing.Any]] = []
        self._installed_tasks: dict[str, dict[str, typing.Any]] = {}

    def add_downsample_task(
        self,
        task: "InfluxDownsampleTask",
        organization_id: str,
        source_bucket_id: str,
        destination_bucket_id: str,
    ):
        """Add the given downsample task as 'not installed'
        to the list of downsample taks

        Args:
            task (InfluxDownsampleTask): The task to add to the mapping
            organization_id (str): Id of the organization the task belongs to
            source_bucket_id (str): The source bucket id for of task
            destination_bucket_id (str): The destination bucket id for the task
        """

        task_dict: dict[str, typing.Any] = self._downsample_task_to_dict(
            task, organization_id, source_bucket_id, destination_bucket_id
        )
        self._not_installed_tasks.append(task_dict)
        self._save()

    def set_task_id(
        self,
        task_id: str,
        task: "InfluxDownsampleTask",
        organization_id: str,
        source_bucket_id: str,
        destination_bucket_id: str,
    ):
        """Sets the task_id for a bucket in the 'not installed' list

        Setting the task id of a 'not installed' task changes the state
        of this task to installed

        Args:
            task_id (str): The id of the given task
            task (InfluxDownsampleTask): The task to change to installed
            organization_id (str): Id of the organization the task belongs to
            source_bucket_id (str): The source bucket id for of task
            destination_bucket_id (str): The destination bucket id for the task
        """
        # pylint: disable=too-many-arguments

        task_dict: dict[str, typing.Any] = self._downsample_task_to_dict(
            task, organization_id, source_bucket_id, destination_bucket_id
        )
        self._not_installed_tasks.remove(task_dict)
        self._installed_tasks[task_id] = task_dict
        self._save()

    def remove_downsample_task(self, task_id: str):
        """Removes information about a installed downsample task

        Args:
            task_id (str): the id of the downsample task to remove
        """
        logger.debug("Remove downsample taks %s", task_id)

        del self._installed_tasks[task_id]
        self._save()

    def _downsample_task_to_dict(
        self,
        task: "InfluxDownsampleTask",
        organization_id: str,
        source_bucket_id: str,
        destination_bucket_id: str,
    ) -> dict[str, typing.Any]:
        return {
            "aggergate_window": int(task.aggregate_window.total_seconds()),
            "aggregate_functions": list(
                map(lambda func: func.name, task.aggregate_functions)
            ),
            "organization_id": organization_id,
            "data_sources": list(map(str, task.data_sources.get_or_default([]))),
            "aggregate_function_filters": list(
                map(
                    lambda func: func.name,
                    task.aggregate_function_filters.get_or_default([]),
                )
            ),
            "source_bucket": source_bucket_id,
            "destination_bucket": destination_bucket_id,
        }

    def _save(self):
        logger.debug("Save downsample mapping")
        downsample_task_mapping_json: dict[str, typing.Any] = {
            "not_installed": self._not_installed_tasks,
            "installed_tasks": self._installed_tasks,
        }

        with open(self._file_path, "w", encoding="utf-8") as file:
            json.dump(downsample_task_mapping_json, file)


class InfluxDownsampleTask(spi.DownsampleTask):
    """Representation of a DownsampleTask to downsample (older) data points"""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        aggregate_window: timedelta,
        aggregate_functions: list[spi.AggregateFunction],
        tasks_api: influx_task_api.TasksApi,
        organization: influx_domain.Organization,
        downsample_task_mapper: DownsampleTaskMapper,
        task_id: str = "",
        data_sources: list[UUID] | None = None,
        aggregate_function_filters: list[spi.AggregateFunction] | None = None,
        source_bucket: spi.Bucket | None = None,
        destination_bucket: spi.Bucket | None = None,
    ) -> None:
        # pylint: disable=too-many-arguments

        super().__init__(
            source_bucket=source_bucket, destination_bucket=destination_bucket
        )
        self._aggregate_window: timedelta = aggregate_window
        self._aggregate_functions: list[spi.AggregateFunction] = aggregate_functions
        self._tasks_api: influx_task_api.TasksApi = tasks_api
        self._organization: influx_domain.Organization = organization
        self._downsample_task_mapper: DownsampleTaskMapper = downsample_task_mapper

        self._task_id: str = task_id

        if data_sources is None:
            self._data_sources = Optional.empty()
        else:
            self._data_sources = Optional.of(frozenset(data_sources))

        if aggregate_function_filters is None:
            self._aggregate_function_filters = Optional.empty()
        else:
            self._aggregate_function_filters = Optional.of(
                frozenset(aggregate_function_filters)
            )

    @property
    def aggregate_function_filters(self):  # TODO Optional typehint
        """Only data created with the given aggregate functions
        are downsampled by this task
        """
        return self._aggregate_function_filters

    @property
    def data_sources(self):  # TODO Optional typehint
        """Only data from the given energy_meter is downsampled by this task

        Note: An empty optional means that all datasources are downsampled
        """
        return self._data_sources

    @property
    def aggregate_window(self) -> timedelta:
        """The time window in which data is aggregated
        using the `aggregate_functions`
        """
        return self._aggregate_window

    @property
    def aggregate_functions(self) -> frozenset[spi.AggregateFunction]:
        """The functions used to aggregate data inside the `aggregate_window`"""
        return frozenset(self._aggregate_functions)

    def _install(self, source_bucket: spi.Bucket, destination_bucket: spi.Bucket):
        task_name: str = (
            f"downsample-{source_bucket.identifier}-to-{destination_bucket.identifier}"
        )

        filter_builder: InfluxFilterBuilder = InfluxFilterBuilder()
        self.data_sources.if_present(filter_builder.filter_source)
        self.aggregate_function_filters.if_present(
            filter_builder.filter_aggregate_function
        )

        env: Environment = Environment(
            loader=PackageLoader(
                "electric_meter_visualizer.consumption_data_store",
                "influx_query_templates",
            )
        )
        template = env.get_template("downsample_task.j2")

        flux_script: str = template.render(
            source_bucket=source_bucket,
            every=self._aggregate_window,
            filter=filter_builder.build(),
            aggregate_function_mapping=AGGREGATE_MAPPING,
            aggregate_functions=self._aggregate_functions,
            aggregate_function_names=set(
                map(AGGREGATE_MAPPING.__getitem__, self._aggregate_functions)
            ),
            aggregate_window=self._aggregate_window,
            destination_bucket=destination_bucket,
        )

        logger.debug("Downsample Task:\n%s", flux_script)

        self._downsample_task_mapper.add_downsample_task(
            self,
            self._organization.id,
            source_bucket.identifier,
            destination_bucket.identifier,
        )

        task: influxdb_client.Task = self._tasks_api.create_task_every(
            task_name,
            flux_script,
            str(int(self._aggregate_window.total_seconds())) + "s",
            self._organization,
        )
        self._task_id = task.id

        self._downsample_task_mapper.set_task_id(
            task.id,
            self,
            self._organization.id,
            source_bucket.identifier,
            destination_bucket.identifier,
        )

    def _uninstall(self):
        if self._task_id is not None:
            self._tasks_api.delete_task(self._task_id)
            self._downsample_task_mapper.remove_downsample_task(self._task_id)
            self._task_id = ""


class InfuxDownsampleTaskBuilder(spi.DownsampleTaskBuilder):
    """Create InfluxDownsampleTaks"""

    def __init__(
        self,
        tasks_api: influx_task_api.TasksApi,
        organization: influx_domain.Organization,
        downsample_task_mapper: DownsampleTaskMapper,
    ) -> None:
        super().__init__()
        self._tasks_api = tasks_api
        self._organization = organization
        self._downsample_task_mapper = downsample_task_mapper

        self._optional_filters: dict[str, typing.Any] = {}

    def filter_aggregate_function(
        self, aggregate_function_list: set[spi.AggregateFunction]
    ) -> spi.DownsampleTaskBuilder:
        self._optional_filters["aggregate_function_filters"] = aggregate_function_list
        return self

    def filter_source(self, id_list: set[UUID]) -> spi.DownsampleTaskBuilder:
        self._optional_filters["data_sources"] = id_list
        return self

    def build(
        self,
        aggregate_window: timedelta,
        aggregate_functions: set[spi.AggregateFunction],
    ) -> InfluxDownsampleTask:
        """Create the DownsampleTask specified with this builder object

        Args:
            aggregate_window (timedelta): time window in which data is aggregated
                                          using the AggregateFunctions
            aggregate_functions (set[AggregateFunction]): `AggregateFunction`s
                    which are used to aggregate the data of each aggregate_window

        Returns:
            DownsampleTask: The DownsampleTask this builder was configured to build
        """

        return InfluxDownsampleTask(
            aggregate_window,
            list(aggregate_functions),
            self._tasks_api,
            self._organization,
            self._downsample_task_mapper,
            **self._optional_filters,
        )


class InfluxConsumptionDataStore(spi.ConsumptionDataStore):
    """
    This class implements the ConsumptionDataStore backed by an InfluxDatabase
    """

    def __init__(self, url: str, token: str, organisation: str):
        super().__init__()
        self.influx_client: influxdb_client.InfluxDBClient = (
            influxdb_client.InfluxDBClient(url=url, token=token, org=organisation)
        )
        self.bucket_api: influx_bucket_api.BucketsApi = self.influx_client.buckets_api()
        self.query_api: influx_query_api.QueryApi = self.influx_client.query_api()
        self.write_api: influx_write_api.WriteApi = self.influx_client.write_api(
            write_options=influx_write_api.SYNCHRONOUS
        )
        self.organisation = organisation

        # Set default_buckets to all buckets
        # This may lead to missing buckets due to pagination
        # https://influxdb-client.readthedocs.io/en/latest/api.html#influxdb_client.BucketsApi.find_buckets
        self.default_buckets: set[spi.Bucket] = {
            InfluxBucket(self.bucket_api, influx_bucket)
            for influx_bucket in self.bucket_api.find_buckets(org=organisation)
        }

    def create_query(self) -> spi.QueryBuilder:
        return InfluxQueryBuilder(
            self.query_api, self.organisation, self.default_buckets
        )

    def put_data(self, datapoint: spi.Datapoint, bucket: spi.Bucket):
        point: influxdb_client.Point = (
            influxdb_client.Point(datapoint.source)
            .field("consumption", datapoint.value)
            .tag("aggregate_function", datapoint.aggregate_function.name)
            .time(datapoint.timestamp)
        )

        self.write_api.write(bucket.identifier, self.organisation, point)

    def delete_data(self, request: spi.DeleteRequest):
        delete_api: influxdb_client.DeleteApi = self.influx_client.delete_api()
        predicate: str = ""

        if request.source.is_present():
            predicate += f'_measurement="{request.source.get()}"'

        if request.source.is_present() and request.aggregate_function.is_present():
            predicate += " AND "

        if request.aggregate_function.is_present():
            predicate += f'aggregate_function="{request.aggregate_function.get().name}"'

        logger.debug("Delete Predicate: %s", predicate)

        delete_api.delete(
            request.start_date,
            request.stop_date,
            predicate,
            request.bucket.identifier,
            self.organisation,
        )

    def delete_bucket(self, bucket: spi.Bucket):
        # TODO implement
        pass

    def close(self):
        self.write_api.close()
        self.influx_client.close()


class InfluxConsumptionDataStoreFactory(
    spi.ConsumptionDataStoreFactory
):  # pylint: disable=too-few-public-methods
    """
    Helper class to create a concrete object of the InfluxConsumptionDataStore
    """

    def create(self) -> spi.ConsumptionDataStore:
        # TODO Implement
        pass
