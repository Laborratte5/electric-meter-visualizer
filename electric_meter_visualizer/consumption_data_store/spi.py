"""
This module represents a storage containing consumption data time series
"""
import abc
from dataclasses import field, dataclass
import enum
from datetime import datetime, timedelta
from uuid import UUID

from optional import Optional


class AggregateFunction(enum.Enum):
    """
    Describes the function that is used to aggregate many datapoints
    into a single datapoint
    """

    RAW = enum.auto()
    SUM = enum.auto()
    AVERAGE = enum.auto()
    MEDIAN = enum.auto()
    MIN = enum.auto()
    MAX = enum.auto()
    QUANTILE = enum.auto()


@dataclass(init=True, frozen=True)
class Datapoint:
    """
    Represents a Datapoint or aggregated Datapoints
    in the ConsumptionDataStore
    """

    source: UUID
    value: float
    timestamp: datetime
    aggregate_function: AggregateFunction


@dataclass(init=True, frozen=True)
class MeasuredDatapoint(Datapoint):
    """Represents a measured datapoint"""

    def __init__(self, source: UUID, value: float, timestamp: datetime):
        super().__init__(source, value, timestamp, AggregateFunction.RAW)


class Query(abc.ABC):
    """
    Abstract representation of a Query used by the ConsumptionDataStore to retrieve data
    """

    @abc.abstractmethod
    def execute(self) -> list[Datapoint]:
        """
        Execute the Query
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __hash__(self):
        raise NotImplementedError


class FilterBuilder(abc.ABC):
    """This interface provides a way to filter
    data (in a Query) stored in a ConsumptionDataStore
    """

    # Do not set the return type of these functions
    # as it is "generic" and should be set only
    # in sub classes

    @abc.abstractmethod
    def filter_aggregate_function(
        self, aggregate_function_list: set[AggregateFunction]
    ):
        """Filter the consumption data based on the AggregateFunction
        that was used to created a DataPoint

        Args:
            aggregate_function_list (set[AggregateFunction]): Only datapoints
            created by AggregateFunctions contained in this list will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def filter_source(self, id_list: set[UUID]):
        """
        Filter the consumption data based on the source id

        Arguments:
            - id_list must be a set of UUIDs
              Only datapoints from sources contained in this list will be returned
        """
        raise NotImplementedError


class Bucket(abc.ABC):
    """Representation of a Bucket in the `ConsumptionDataStore`

    A bucket is a container for data in the ConsumptionDataStore,
    each `Datapoint` is inserted in one Bucket.
    A bucket can have a retention period which describes the time window
    datapoints in this bucket are garanteed not to be deleted.
    If a Datapoint is older than the given retention period based on the
    current date, the datapoint may be deleted at any time.
    A bucket can also have a `DownsampleTask` which is executed periodically
    to aggregate data inside this bucket and put the results into another bucket
    with a longer retention period.
    """

    def __init__(self):
        self._retention_period: timedelta = timedelta(seconds=0)
        self._downsample_tasks_mapping: dict["DownsampleTask", "Bucket"] = {}

    @property
    def retention_period(self) -> timedelta:
        """The time data is garanteed to reside in this bucket before it is deleted.

        A retention_period of zero seconds indicates no retention.

        Returns:
            timedelta: The current retention period
        """
        return self._retention_period

    @retention_period.setter
    def retention_period(self, retention_period: timedelta) -> None:
        """Sets the new retention period for this bucket

        Setting a new retention period for a bucket also affects data that was
        inserted before the change of the retention period.

        A retention_period of zero seconds indicates no retention.

        Args:
            retention_period (timedelta): The time data is garanteed to reside in this bucket
                                          before it is deleted.
        """
        self._set_retention_period(retention_period)
        self._retention_period = retention_period

    @abc.abstractmethod
    def _set_retention_period(self, retention_period: timedelta) -> None:
        """Sets the new retention period for this bucket

        Implementors of this spi should use this method to register the retention period.

        Args:
            retention_period (timedelta): The time data is garanteed to resied in this bucket
                                          before it is deleted.
        """
        raise NotImplementedError

    @property
    def downsample_tasks(self) -> list["DownsampleTask"]:
        """A list with the current DownsampleTasks

        Returns:
            list[DownsampleTask]: An list with the current DownsampleTaks
                                  of this bucket
        """
        return list(self._downsample_tasks_mapping.keys())

    def set_downsample_task(
        self, task: "DownsampleTask", destination_bucket: "Bucket"
    ) -> None:
        """Add a new DownsampleTask with the given destination Bucket

        If the given task is not already in this buckets task list,
        add the task with the given destination bucket.
        If the given task already is in this buckets task list,
        set the desination bucket of this task to the new given
        `destination_bucket`

        Args:
            task (DownsampleTask): The new or already exisiting DownsampleTask
            destination_bucket (Bucket): The new destination bucket for the given
                                         DownsampleTask
        """

        if task in self.downsample_tasks:
            # Remove destination for existing task
            existing_destination: "Bucket" = self._downsample_tasks_mapping[task]
            task.uninstall(self, existing_destination)

        # Add task with new destination
        task.install(self, destination_bucket)
        self._downsample_tasks_mapping[task] = destination_bucket

    def remove_downsample_task(self, task: "DownsampleTask") -> None:
        """Remove the given DownsampleTask from this bucket

        If the given DownsampleTaks does not exist in this Bucket
        this method does not change anything.

        Args:
            task (DownsampleTask): The DownsampleTask that should be removed
        """
        self._downsample_tasks_mapping.pop(task, None)

    def get_dowsample_task_destination(self, task: "DownsampleTask") -> Optional:
        """Return an Optional with the given DownsampelTasks destination Bucket

        Args:
            task (DownsampleTask): The task of which the destination Bucket
                                   should be returned

        Returns:
            Optional: Containing the destination Bucket if the given DownsampleTask
                      was added to this Bucket or an empty Optional if the given task
                      never was added to this Bucket
        """

        if task in self.downsample_tasks:
            return Optional.of(self._downsample_tasks_mapping[task])
        return Optional.empty()


class QueryBuilder(FilterBuilder):
    """
    Used to create concrete Query objects
    """

    @abc.abstractmethod
    def filter_bucket(self, bucket_list: set[Bucket]) -> "QueryBuilder":
        """
        Filter the consumption data based on the buckets this data resides

        Arguments:
            - bucket_list must be a set of Bucket
              Only datapoints from a bucket contained in this list will be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    def filter_aggregate_function(
        self, aggregate_function_list: set[AggregateFunction]
    ) -> "QueryBuilder":
        raise NotImplementedError

    @abc.abstractmethod
    def filter_source(self, id_list: set[UUID]) -> "QueryBuilder":
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


@dataclass
class DeleteRequest:
    """Class encapsulating mandatory and optional parameters used when
    deleting Datapoints from a ConsumptionDataStore
    """

    bucket: Bucket
    start_date: datetime
    stop_date: datetime
    _source: Optional = field(init=False, default=Optional.empty())
    _aggregate_function: Optional = field(init=False, default=Optional.empty())

    @property
    def source(self):
        """Optional containing the source to which the DeleteRequest is limited"""
        return self._source

    @source.setter
    def source(self, source: UUID):
        if source:
            self._source = Optional.of(source)
        else:
            self._source = Optional.empty()

    @property
    def aggregate_function(self):
        """Optional containing the AggregateFunction to which the DeleteRequest is limited"""
        return self._aggregate_function

    @aggregate_function.setter
    def aggregate_function(self, aggregate_function: AggregateFunction):
        if aggregate_function:
            self._aggregate_function = Optional.of(aggregate_function)
        else:
            self._source = Optional.empty()


class DownsampleTask(abc.ABC):
    """A downsample task which specifies how to downsample (older) data points"""

    @abc.abstractmethod
    def install(self, source_bucket: Bucket, destination_bucket: Bucket):
        """Install this DownsampleTask with the specified `source_bucket` and `destination_bucket`

        Note: This method should never be called outside of the spi implementation
              Use `set_downsample_task` of Bucket instead.

        Args:
            source_bucket (Bucket): Bucket containing the data that should be downsampled
            destination_bucket (Bucket): Bucket the downsampled results will be put
        """
        raise NotImplementedError

    @abc.abstractmethod
    def uninstall(self, source_bucket: Bucket, destination_bucket: Bucket):
        """Uninstall this DownsampleTask between `source_bucket` and `destination_bucket`

        Note: This method should never be called outside of the spi implementation
              Use `clear_downsample_task` of Bucket instead.

        Args:
            source_bucket (Bucket): Bucket containing the data that should be downsampled
            destination_bucket (Bucket): Bucket the downsampled results will be put
        """
        raise NotImplementedError


class DownsampleTaskBuilder(FilterBuilder):
    """Used to create concrete DownsampleTask objects"""

    @abc.abstractmethod
    def filter_aggregate_function(
        self, aggregate_function_list: set[AggregateFunction]
    ) -> "DownsampleTaskBuilder":
        raise NotImplementedError

    @abc.abstractmethod
    def filter_source(self, id_list: set[UUID]) -> "DownsampleTaskBuilder":
        raise NotImplementedError

    @abc.abstractmethod
    def build(
        self, aggregate_window: timedelta, aggregate_functions: set[AggregateFunction]
    ) -> None:
        """Create the DownsampleTask specified with this builder object

        Args:
            aggregate_window (timedelta): time window in which data is aggregated
                                          using the AggregateFunctions
            aggregate_functions (set[AggregateFunction]): `AggregateFunction`s
                    which are used to aggregate the data of each aggregate_window
        """
        raise NotImplementedError


class ConsumptionDataStore(abc.ABC):
    """
    This class is used to abstract the interaction with a ConsumptionDataStore
    It provides methods to create, retrieve and delete consumption data points
    """

    @abc.abstractmethod
    def create_query(self) -> QueryBuilder:
        """
        Create a new QueryBuild

        Returns: new QueryBuilder instance
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_bucket(self, name: str) -> Bucket:
        """Create a new Bucket and add it to this ConsumptionDataStore

        Args:
            name (str): The name of the new Bucket

        Returns:
            Bucket: The new created Bucket
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def buckets(self) -> list[Bucket]:
        """List of Buckets in this ConsumptionDataStore

        Returns:
            list[Bucket]: Buckets in this ConsumptionDataStore
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_downsample_task(self) -> DownsampleTaskBuilder:
        """Create a new DownsampleTaskBuilder for this ConsumptionDataStore

        Returns:
            DownsampleTaskBuilder: A DownsampleTaskBuilder for the specific
                implementation of this ConsumptionDataStore
        """
        raise NotImplementedError

    @abc.abstractmethod
    def put_data(self, datapoint: Datapoint, bucket: Bucket):
        """
        Store a Datapoint in the specified bucket of this ConsumptionDataStore

        Arguments:
            - datapoint must be a Datapoint
              The Datapoint that should be stored in this ConsumptionDataStore
            - bucket must be a Bucket
              The Bucket the data should be put in. The Bucket must already exist
              in the ConsumptionDataStore
        """
        raise NotImplementedError

    def put_data_batch(self, datapoints: set[Datapoint], bucket: Bucket):
        """Store multiple Datapoints in the specified bucket of this ConsumptionDataStore

        Note: This method has a default implementation, which simply loops over the datapoints
              and inserts them one after another, and thus can be used even if the
              spi does not support batch operations.
              However spi Implementors are strongly encouraged to override the default
              implementation with a more performant approach.

        Args:
            datapoints (set[Datapoint]): Datapoints that should be added to the Bucket
            bucket (Bucket): The Bucket the datapoints will be stored in
        """
        for datapoint in datapoints:
            self.put_data(datapoint, bucket)

    @abc.abstractmethod
    def delete_data(self, request: DeleteRequest):
        """Delete data from this ConsumptionDataStore

        Args:
            request (DeleteRequest): Description of which data should be deleted
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_bucket(self, bucket: Bucket):
        """Delete a bucket with all datapoints from this ConsumptionDataStore

        Args:
            bucket (Bucket): the bucket that should be deleted
        """
        raise NotImplementedError

    def close(self):
        """Close this ConsumptionDataStore

        Close this ConsumptionDataStore an release all resources that got aquired
        during the usage of this ConsumptionDataStore.
        After `close()` was called no further calls to this object are allowed
        """


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
