"""This module is a concrete implementation of the spi module based on InfluxDB
"""
# pylint: disable=fixme
from uuid import UUID
from datetime import datetime
from datetime import timedelta
import influxdb_client as influx
from electric_meter_visualizer.consumption_data_store import spi


class InfluxQuery(spi.Query):
    """
    Representation of a Flux query
    """

    def __init__(self, query_api: influx.QueryApi, bucket: str, query: str):
        # TODO implement
        pass

    def execute(self) -> list[spi.Datapoint]:
        # TODO implement
        pass

    def __hash__(self):
        # TODO implement
        pass


class InfluxQueryBuilder(spi.QueryBuilder):
    """
    Helper class to build InfluxQuery objects
    """

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
