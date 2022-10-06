"""
This module represents a storage containing consumption data time series
"""
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
