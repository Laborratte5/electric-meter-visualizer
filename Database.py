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

    def __init__(self):
        # TODO
        pass

    def add_data_src(self, data_src_name):
        # TODO
        pass

    def remove_data_src(self, data_src_name):
        # TODO
        pass

    def get_day(self, delta=0):
        # get data for each datasource and put it in a dict
        pass

    def get_week(self, delta=0):
        # get data for each datasource and put it in a dict
        pass

    def get_month(self, delta=0):
        # get data for each datasource and put it in a dict
        pass

    def get_year(self, delta=0):
        # get data for each datasource and put it in a dict
        pass

    def get_years(self, delta=0):
        # get data for each datasource and put it in a dict
        pass

class Archive:

    def __init__(self, data_per_day, keep_day, data_per_week, keep_week, data_per_month, keep_month,
                 data_per_year, keep_year, keep_years):
        # Data per x
        self.dpd = data_per_day
        self.dpw = data_per_week
        self.dpm = data_per_month
        self.dpy = data_per_year
        # Keep x data
        self.keep_day = keep_day
        self.keep_week = keep_week
        self.keep_month = keep_month
        self.keep_year = keep_year
        self.keep_years = keep_years
        # counter
        self.day_counter = 0
        self.week_counter = 0
        self.month_counter = 0
        self.year_counter = 0
        self.years_counter = 0
        # sums
        self.day_sum = 0
        self.week_sum = 0
        self.month_sum = 0
        self.year_sum = 0
        self.years_sum = 0
        # Data archives
        self.day = []
        self.week = []
        self.month = []
        self.year = []
        self.years = []

    def add_data(self, data):
        self.day_counter += 1
        self.day_sum += data

        self.week_counter += 1
        self.week_sum += data

        self.month_counter += 1
        self.month_sum += data

        self.year_counter += 1
        self.year_sum += data

        self.years_counter += 1
        self.years_sum += 1

        timestamp = datetime.now().timestamp()

        if self.day_counter == 1:
            self.day.append((self.day_sum, timestamp))
            if len(self.day) > self.keep_day:
                self.day.pop(0)  # Drop oldest value
            self.day_counter = 0
            self.day_sum = 0

        if self.week_counter == self.dpd:
            self.week.append((self.week_sum, timestamp))
            if len(self.week) > self.keep_week:
                self.week.pop(0)  # Drop oldest value
            self.week_counter = 0
            self.week_sum = 0

        if self.month_counter == self.dpw:
            self.month.append((self.month_sum, timestamp))
            if len(self.month) > self.keep_month:
                self.month.pop(0)  # Drop oldest value
            self.month_counter = 0
            self.month_sum = 0

        if self.year_counter == self.dpm:
            self.year.append((self.year_sum, timestamp))
            if len(self.year) > self.keep_year:
                self.year.pop(0)
            self.year_counter = 0
            self.year_sum = 0

        if self.years_counter == self.dpy:
            self.years.append((self.year_sum, timestamp))
            if len(self.years) > self.keep_years:
                self.years.pop(0)
            self.years_counter = 0
            self.years_sum = 0

    def get_day(self, delta=0):
        return self.day

    def get_week(self, delta=0):
        return self.week

    def get_month(self, delta=0):
        return self.month

    def get_year(self, delta=0):
        return self.year

    def get_years(self, delta=0):
        return self.years
