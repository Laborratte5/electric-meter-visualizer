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


class RetentionPolicy(abc.ABC):  # pylint: disable=R0903
    """
    Representation of a retention policy
    which specifies how to handle (older) data points
    """

    @abc.abstractmethod
    def execute(self):
        """
        Executes this retention policy
        Depending on the retention policy this
        leads to data points being deleted or aggregated
        """
        raise NotImplementedError


class ConsumptionDataStore(abc.ABC):
    """
    This class is used to abstract the interaction with a ConsumptionDataStore
    It provides methods to create, retrieve and delete consumption data points
    """

    def __init__(self):
        self.__retention_policies: list[RetentionPolicy] = []

    def add_retention_policy(self, retention_policy: RetentionPolicy):
        """
        Add a retention policy to this ConsumptionDataStore

        All RetentionPolicies can be executed using the execute_retention_policy funtion
        Note that individual RetentionPolicies still can be executed on demand using the
        RetentionPolicy.execute() function

        Arguments:
            - retention_policy must be RetentionPolicy
              The RetentionPolicy that should be added
        """
        self.__retention_policies.append(retention_policy)

    def remove_retention_policy(self, retention_policy: RetentionPolicy):
        """
        Remove a retention policy from this ConsumptionDataStore

        Note that individual RetentionPolicies still can be executed on demand using the
        RetentionPolicy.execute() function

        Arguments:
            - retention_policy must be RetentionPolicy
              The RetentionPolicy that should be removed
        """
        self.__retention_policies.remove(retention_policy)

    def execute_retention_policy(self):
        """
        Execute all retention policies added to this ConsumptionData

        Note that individual RetentionPolicies still can be executed on demand using the
        RetentionPolicy.execute() function
        """
        for retention_policy in self.__retention_policies:
            retention_policy.execute()

    @abc.abstractmethod
    def create_query(self) -> QueryBuilder:
        """
        Create a new QueryBuild

        Returns: new QueryBuilder instance
        """
        raise NotImplementedError

    @abc.abstractmethod
    def put_data(self, datapoint: Datapoint, bucket: str):
        """
        Store a Datapoint in the specified bucket of this ConsumptionDataStore

        Arguments:
            - datapoint must be a Datapoint
              The Datapoint that should be stored in this ConsumptionDataStore
            - bucket must be a string
              The name of the bucket the data should be put in
              If no bucket with a given name exists a new bucket is created
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_data(self, datapoint: Datapoint, bucket: str):
        """
        Delete a Datapoint from this ConsumptionDataStore

        Arguments:
            - datapoint must be a Datapoint
              The Datapoint that should be deleted from this ConsumptionDataStore
            - bucket must be a string
              The name of the bucket the data should be deleted from
        """
        raise NotImplementedError


class BaseRetentionPolicy(RetentionPolicy):  # pylint: disable=R0903
    """
    Basic RetentionPolicy

    This is the base class for simple RetentionPolicies with the following algorithm:
    - get_data, used to return all relevant Datapoints
    - aggregate, used to aggregate the datapoints based on the desired RetentionPolicy
    - store, used to store the new aggregated Datapoints
    - remove, used to remove the old datapoints based on the desired RetentionPolicy

    Member variables:
        - datastore a ConsumptionDataStore
          Data store to which this RetentionPolicy applies
        - source_bucket
          Source bucket to which this RetentionPolicy applies
        - destination_bucket
          if this RetentionPolicy aggregates data from the source_bucket the aggregated
          data should be written into the destination bucket
    """

    def __init__(
        self,
        datastore: ConsumptionDataStore,
        source_bucket: str,
        destination_bucket: str,
    ):
        self.datastore: ConsumptionDataStore = datastore
        self.source_bucket: str = source_bucket
        self.destination_bucket: str = destination_bucket

    def execute(self):
        """
        Execute this RetentionPolicy by running the algorithm described above
        """
        data: list[Datapoint] = self._get_data()
        aggregated_data: list[Datapoint] = self._aggregate(data)
        self._store(aggregated_data)
        self._remove(data)

    def _get_data(self) -> list[Datapoint]:
        """
        Returns all Datapoints that are relevant for this RetentionPolicy

        Returns: list of relevant Datapoints
        """
        raise NotImplementedError

    def _aggregate(self, data_points: list[Datapoint]) -> list[Datapoint]:
        """
        Aggregates the given data according to retention policy

        Arguments:
            - data_points list of Datapoints
              The Datapoints that should be aggregated according to this retention policy

        Returns: list of aggregated Datapoints
        """
        raise NotImplementedError

    def _store(self, result: list[Datapoint]):
        """
        Stores the given data into the destination_bucket of this RetentionPolicy

        Arguments:
            - result list of Datapoints
              The processed Datapoints that should be stored into the destation_bucket
        """
        raise NotImplementedError

    def _remove(self, old_data: list[Datapoint]):
        """
        Removes old Datapoints from this RetentionPolicy

        Removes the old Datapoints (that got aggregated)
        from the source_bucket of this RetentionPolicy

        Arguments:
            - old_data list of Datapoints
              The old Datapoints that should be removed from the source_bucket
        """
        raise NotImplementedError


class ConsumptionDataStoreFactory(abc.ABC):  # pylint: disable=R0903
    """
    Used to initiate a concrete ConsumptionDataStore implementation
    """

    def create(self) -> ConsumptionDataStore:
        """
        Creates and initialize a concrete ConsumptionDataStore

        Returns: Initialized instance of a concrete ConsumptionDataStore implementation
        """
        raise NotImplementedError