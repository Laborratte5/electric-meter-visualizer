"""
This module represents a storage containing consumption data time series
"""
import abc
from dataclasses import dataclass
import enum
from datetime import datetime, timedelta


class AggregateFunction(enum.Enum):
    """
    Describes the function that is used to aggregate many datapoints
    into a single datapoint
    """

    SUM = enum.auto()
    AVERAGE = enum.auto()
    MEAN = enum.auto()
    MIN = enum.auto()
    MAX = enum.auto()
    QUANTILE = enum.auto()


@dataclass(init=True, frozen=True)
class Datapoint:
    """
    Represents a Datapoint or aggregated Datapoints
    in the ConsumptionDataStore
    """

    timestamp: datetime
    timespan: timedelta
    value: dict[str, float]


class Query(abc.ABC):
    """
    Abstract representation of a Query used by the ConsumptionDataStore to retrieve data
    """

    @abc.abstractmethod
    def execute(self):
        """
        Execute the Query
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __hash__(self):
        raise NotImplementedError


class QueryBuilder(abc.ABC):
    """
    Used to create concrete Query objects
    """

    @abc.abstractmethod
    def filter_bucket(self, bucket_list: set[str]) -> "QueryBuilder":
        """
        Filter the consumption data based on the buckets this data resides

        Arguments:
            - bucket_list must be a set of string
              Only datapoints from a bucket contained in this list will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def filter_source(self, id_list: set[int]) -> "QueryBuilder":
        """
        Filter the consumption data based on the source id

        Arguments:
            - id_list must be a set of int
              Only datapoints from sources contained in this list will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def filter_start(self, start_date: datetime) -> "QueryBuilder":
        """
        Filter the consumption data based on the start_date of the measurement

        Arguments:
            - start_date must be datetime
              Only datapoints with a timestamp at start_date or later will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def filter_stop(self, stop_date: datetime) -> "QueryBuilder":
        """
        Filter the consumption data basaed on the stop_date of the measurement

        Arguments:
            - stop_date must be datetime
              Only datapoints with a timestamp earlier than stop_date will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def build(
        self, aggregate_window: timedelta, aggregate_functions: set[AggregateFunction]
    ) -> Query:
        """
        Create the Query specified with this builder object

        Arguments:
            - aggregate_window must be timedelta
              Datapoints are grouped into this aggregate_window based on their timestamp
            - aggregate_functions must be a set of AggregateFunctions
              All Datapoints inside an aggregate_window will be aggregated using the functions
              in aggregate_functions.
              The result will contain one datapoint for each aggregate_window.
              The resulting datapoints contain one value for each aggregate_function.
        """
        raise NotImplementedError
