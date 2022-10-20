"""This module is a concrete implementation of the spi module based on InfluxDB
"""
# pylint: disable=fixme
from uuid import UUID
from datetime import datetime
from datetime import timedelta
import influxdb_client.client.query_api as influx_query_api
from electric_meter_visualizer.consumption_data_store import spi


class InfluxQuery(spi.Query):
    """
    Representation of a Flux query
    """

    def __init__(self, query_api: influx_query_api.QueryApi, bucket: str, query: str):
        """Create a new Query for an InfluxConsumptionDataStore

        Args:
            query_api (influxdb_client.client.query_api.QueryApi):
                Query API that is used to execute this query
            bucket (str): the identifier for the bucket on which this query is executed
            query (str): the Flux query string this query should execute
        """
        self.query_api: influx_query_api.QueryApi = query_api
        self.bucket: str = bucket
        self.query: str = query

    def execute(self) -> list[spi.Datapoint]:
        """Execute this query

        Returns:
            list[spi.Datapoint]: parsed query result
        """
        # TODO implement

    def __hash__(self):
        # TODO implement
        pass


class InfluxQueryBuilder(spi.QueryBuilder):
    """
    Helper class to build InfluxQuery objects
    """

    def __init__(self, query_api: influx_query_api.QueryApi, default_bucket: str):
        self.query_api: influx_query_api.QueryApi = query_api
        self._buckets: list[str] = [default_bucket]
        self._source_filters: str = ""
        self._start_date = None
        self._stop_date = None

    def filter_bucket(self, bucket_list: set[str]) -> spi.QueryBuilder:
        # TODO implement
        pass

    def filter_source(self, id_list: set[UUID]) -> spi.QueryBuilder:
        # TODO implement
        pass

    def filter_start(self, start_date: datetime) -> spi.QueryBuilder:
        # TODO implement
        pass

    def filter_stop(self, stop_date: datetime) -> spi.QueryBuilder:
        # TODO implement
        pass

    def build(
        self,
        aggregate_window: timedelta,
        aggregate_functions: set[spi.AggregateFunction],
    ) -> spi.Query:
        # TODO implement
        pass


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


class InfluxConsumptionDataStoreFactory(
    spi.ConsumptionDataStoreFactory
):  # pylint: disable=R0903
    """
    Helper class to create a concrete object of the InfluxConsumptionDataStore
    """

    def create(self) -> spi.ConsumptionDataStore:
        # TODO implement
        pass
