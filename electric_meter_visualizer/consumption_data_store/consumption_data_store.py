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
