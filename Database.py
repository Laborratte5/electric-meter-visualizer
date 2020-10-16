from datetime import datetime


class Database:
    @classmethod
    def create_database(cls):
        # TODO
        pass

    @classmethod
    def load_database(cls):
        # TODO
        pass

    def __init__(self, data_per_hour, keep_raw, keep_day, keep_month, keep_year, keep_years):
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

    def remove_data_src(self, data_src_name):
        # TODO
        del self.datasources[data_src_name]
        pass

    def add_data(self, data, data_src):
        #TODO
        self.datasources[data_src].add_data(data)
        pass

    # TODO delta
    def get_raw(self, delta=0):
        # get data for each datasource and put it in a dict
        return {data_src: data.get_raw() for data_src, data in self.datasources.items()}

    def get_day(self, delta=0):
        # get data for each datasource and put it in a dict
        return {data_src: data.get_day() for data_src, data in self.datasources.items()}

    def get_month(self, delta=0):
        # get data for each datasource and put it in a dict
        return {data_src: data.get_month() for data_src, data in self.datasources.items()}

    def get_year(self, delta=0):
        # get data for each datasource and put it in a dict
        return {data_src: data.get_year() for data_src, data in self.datasources.items()}

    def get_years(self, delta=0):
        # get data for each datasource and put it in a dict
        return {data_src: data.get_years() for data_src, data in self.datasources.items()}


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

        timestamp = datetime.now().timestamp()

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

    def get_raw(self, delta=0):
        return self.raw

    def get_day(self, delta=0):
        return self.day

    def get_month(self, delta=0):
        return self.month

    def get_year(self, delta=0):
        return self.year

    def get_years(self, delta=0):
        return self.years
