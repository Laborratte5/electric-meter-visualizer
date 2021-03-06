import json
from datetime import datetime


class Database:

    @classmethod
    def create_database(cls, file_name, data_per_hour, keep_raw, keep_day, keep_month, keep_year, keep_years):
        with open(file_name, 'w') as f:
            f.close()
        database = Database(file_name, data_per_hour, keep_raw, keep_day, keep_month, keep_year, keep_years)
        database._save_database()
        return database

    @classmethod
    def load_database(cls, file):
        with open(file) as f:
            decoder = DatabaseJsonDecoder()
            database = json.load(f, object_hook=decoder.decode)
            database.file = file
            return database

    def __init__(self, file, data_per_hour, keep_raw, keep_day, keep_month, keep_year, keep_years):
        self.sync_file = True  # TODO
        self.file = file
        self.dph = data_per_hour
        self.keep_raw = keep_raw
        self.keep_day = keep_day
        self.keep_month = keep_month
        self.keep_year = keep_year
        self.keep_years = keep_years

        self.datasources = {}

    def add_data_src(self, data_src_name):
        self.datasources[data_src_name] = Archive(self.dph, self.keep_raw, self.keep_day,
                                                  self.keep_month, self.keep_year, self.keep_years)
        self._save_database()

    def remove_data_src(self, data_src_name):
        del self.datasources[data_src_name]
        self._save_database()

    def add_data(self, data, data_src):
        self.datasources[data_src].add_data(data)
        self._save_database()

    def _save_database(self):
        if self.sync_file:
            with open(self.file, 'w') as f:
                json.dump(self, f, cls=DatabaseJsonEncoder)

    # Getter
    def get_raw(self, since=None, until=None):
        self.assert_since_until(since, until)
        # get data for each datasource and put it in a dict
        return {data_src: [{'value': value, 'timestamp': timestamp} for value, timestamp in data.get_raw()
                           if self.check_timestamp(timestamp, since, until)
                           ]
                for data_src, data in self.datasources.items()}

    def get_day(self, since=None, until=None):
        self.assert_since_until(since, until)
        # get data for each datasource and put it in a dict
        return {data_src: [{'value': value, 'timestamp': timestamp} for value, timestamp in data.get_day()
                           if self.check_timestamp(timestamp, since, until)
                           ]
                for data_src, data in self.datasources.items()}

    def get_month(self, since=None, until=None):
        self.assert_since_until(since, until)
        # get data for each datasource and put it in a dict
        return {data_src: [{'value': value, 'timestamp': timestamp} for value, timestamp in data.get_month()
                           if self.check_timestamp(timestamp, since, until)
                           ]
                for data_src, data in self.datasources.items()}

    def get_year(self, since=None, until=None):
        self.assert_since_until(since, until)
        # get data for each datasource and put it in a dict
        return {data_src: [{'value': value, 'timestamp': timestamp} for value, timestamp in data.get_year()
                           if self.check_timestamp(timestamp, since, until)
                           ]
                for data_src, data in self.datasources.items()}

    def get_years(self, since=None, until=None):
        self.assert_since_until(since, until)
        # get data for each datasource and put it in a dict
        return {data_src: [{'value': value, 'timestamp': timestamp} for value, timestamp in data.get_years()
                           if self.check_timestamp(timestamp, since, until)]
                for data_src, data in self.datasources.items()}

    def assert_since_until(self, since, until):
        if since is not None and until is not None and until < since:
            raise ValueError

    def check_timestamp(self, timestamp, since, until):
        return (since is None or since <= timestamp) and (until is None or timestamp <= until)


class Archive:

    def __init__(self, data_per_hour, keep_raw, keep_day, keep_month, keep_year, keep_years):
        # Data per hour
        self.dph = data_per_hour
        # Keep data
        self.keep_raw = keep_raw
        self.keep_day = keep_day
        self.keep_month = keep_month
        self.keep_year = keep_year
        self.keep_years = keep_years
        # counter
        self.day_counter = 0
        self.month_counter = 0
        self.year_counter = 0
        self.years_counter = 0
        # sums
        self.day_sum = 0
        self.month_sum = 0
        self.year_sum = 0
        self.years_sum = 0
        # Data archives
        self.raw = []
        self.day = []
        self.month = []
        self.year = []
        self.years = []

    def add_data(self, data):
        self.day_counter += 1
        self.day_sum += data

        self.month_counter += 1
        self.month_sum += data

        self.year_counter += 1
        self.year_sum += data

        self.years_counter += 1
        self.years_sum += data

        timestamp = datetime.now()

        # Add raw
        self.raw.append((data, timestamp))
        if len(self.raw) > self.keep_raw:
            self.raw.pop(0)

        # Day
        if self.day_counter == self.dph:  # One hour passed
            self.day.append((self.day_sum, timestamp))
            if len(self.day) > self.keep_day:
                self.day.pop(0)  # Drop oldest value
            self.day_counter = 0
            self.day_sum = 0

        # Month
        if self.month_counter == self.dph * 24:  # One day passed
            self.month.append((self.month_sum, timestamp))
            if len(self.month) > self.keep_month:
                self.month.pop(0)  # Drop oldest value
            self.month_counter = 0
            self.month_sum = 0

        # Year
        if self.year_counter == self.dph * 30 * 24:  # One month passed
            self.year.append((self.year_sum, timestamp))
            if len(self.year) > self.keep_year:
                self.year.pop(0)
            self.year_counter = 0
            self.year_sum = 0

        if self.years_counter == self.dph * 24 * 365:   # One year passed
            self.years.append((self.years_sum, timestamp))
            if len(self.years) > self.keep_years:
                self.years.pop(0)
            self.years_counter = 0
            self.years_sum = 0

    def get_raw(self, since=None, until=None):
        return self.raw

    def get_day(self, since=None, until=None):
        return self.day + [(self.day_sum, datetime.now())]

    def get_month(self, since=None, until=None):
        return self.month + [(self.month_sum, datetime.now())]

    def get_year(self, since=None, until=None):
        return self.year + [(self.year_sum, datetime.now())]

    def get_years(self, since=None, until=None):
        return self.years + [(self.years_sum, datetime.now())]


# TODO refactor use marshmallow
class DatabaseJsonEncoder(json.JSONEncoder):

    def encode_database(self, db):
        return {
            'data_per_hour': db.dph,
            'keep_raw': db.keep_raw,
            'keep_day': db.keep_day,
            'keep_month': db.keep_month,
            'keep_year': db.keep_year,
            'keep_years': db.keep_years,
            'data_sources': [{
                'id': name,
                'data': data
                } for name, data in db.datasources.items()]
        }

    def encode_archive(self, archive):
        return {
            'day_counter': archive.day_counter,
            'month_counter': archive.month_counter,
            'year_counter': archive.year_counter,
            'years_counter': archive.years_counter,
            # sums
            'day_sum': archive.day_sum,
            'month_sum': archive.month_sum,
            'year_sum': archive.year_sum,
            'years_sum': archive.years_sum,
            # Data archives
            'raw_data': archive.raw,
            'day_data': archive.day,
            'month_data': archive.month,
            'year_data': archive.year,
            'years_data': archive.years
        }

    def default(self, o):
        if isinstance(o, Database):
            # Database to dict
            return self.encode_database(o)
        elif isinstance(o, Archive):
            # Archive to dict
            return self.encode_archive(o)
        elif isinstance(o, datetime):
            # Datetime to string
            return o.isoformat()
        else:
            return json.JSONEncoder.default(self, o)


# TODO refactor use marshmallow
class DatabaseJsonDecoder:

    def __init__(self):
        self.datasources = {}

    def is_database(self, o):
        return all(i in ('data_per_hour', 'keep_raw', 'keep_day', 'keep_month', 'keep_year', 'keep_years',
                         'data_sources')
                   for i in o.keys())

    def is_datasource(self, o):
        return all(i in ('id', 'data') for i in o.keys())

    def is_data(self, o):
        return all(i in ('day_counter',  'month_counter',  'year_counter',  'years_counter',  'day_sum',  'month_sum',
                         'year_sum',  'years_sum',  'raw_data', 'day_data', 'month_data', 'year_data', 'years_data')
                   for i in o.keys())

    def decode_database(self, database_dict):
        # Decode Database
        dph = database_dict['data_per_hour']
        keep_raw = database_dict['keep_raw']
        keep_day = database_dict['keep_day']
        keep_month = database_dict['keep_month']
        keep_year = database_dict['keep_year']
        keep_years = database_dict['keep_years']
        datasources = {}
        for datasource_dict in database_dict['data_sources']:
            for key, value in datasource_dict.items():
                datasources[key] = value

        database = Database(None, dph, keep_raw, keep_day, keep_month, keep_year, keep_years)
        for name, ds in datasources.items():
            datasources[name] = Archive(dph, keep_raw, keep_day, keep_month, keep_year, keep_years)
            datasources[name].day_counter = ds.day_counter
            datasources[name].month_counter = ds.month_counter
            datasources[name].year_counter = ds.year_counter
            datasources[name].years_counter = ds.years_counter
            # sums
            datasources[name].day_sum = ds.day_sum
            datasources[name].month_sum = ds.month_sum
            datasources[name].year_sum = ds.year_sum
            datasources[name].years_sum = ds.years_sum
            # Data archives
            datasources[name].raw = ds.raw
            datasources[name].day = ds.day
            datasources[name].month = ds.month
            datasources[name].year = ds.year
            datasources[name].years = ds.years
        database.datasources = datasources
        return database

    def decode_datasource(self, datasource_dict):
        name = datasource_dict['id']
        data = datasource_dict['data']
        self.datasources[name] = data
        return {name: data}

    def decode_data(self, data_dict):
        a = Archive(0, 0, 0, 0, 0, 0)
        a.day_counter = data_dict['day_counter']
        a.month_counter = data_dict['month_counter']
        a.year_counter = data_dict['year_counter']
        a.years_counter = data_dict['years_counter']
        # sums
        a.day_sum = data_dict['day_sum']
        a.month_sum = data_dict['month_sum']
        a.year_sum = data_dict['year_sum']
        a.years_sum = data_dict['years_sum']
        # Data archives
        a.raw = self.decode_data_to_tuple(data_dict['raw_data'])
        a.day = self.decode_data_to_tuple(data_dict['day_data'])
        a.month = self.decode_data_to_tuple(data_dict['month_data'])
        a.year = self.decode_data_to_tuple(data_dict['year_data'])
        a.years = self.decode_data_to_tuple(data_dict['years_data'])
        return a

    # Convert json list into python tuple
    def decode_data_to_tuple(self, data_list):
        return [(value, datetime.fromisoformat(timestamp)) for value, timestamp in data_list]

    def decode(self, o):
        if self.is_data(o):
            # deserialize data
            return self.decode_data(o)
        elif self.is_datasource(o):
            # deserialize datasource
            return self.decode_datasource(o)
        elif self.is_database(o):
            # deserialize database
            return self.decode_database(o)
        else:
            raise ValueError('Error decoding database file')