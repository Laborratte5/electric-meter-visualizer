import threading
import time

from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup
import os
import schedule

from Database import Database


def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


class Logic:

    def __init__(self, development):
        self.development = development
        self.next_id = 0  # TODO letzte id aus datei laden
        self.electric_meters = {}  # TODO aus datei laden
        self.config = {}  # TODO aus config laden

        # TODO aus config laden
        database_file = 'database.json'
        self.data_per_hour = 3600

        if os.path.isfile(database_file):
            #pass

            # TODO
            self.database = Database.load_database(database_file)
            print('database file exists')
        else:
            print('database file doesnt exist')
            # TODO aus config laden
            self.keep_raw = 10
            self.keep_day = 48
            self.keep_month = 30
            self.keep_year = 12
            self.keep_years = 3
            # Create Database
            self.database = Database.create_database(database_file, self.data_per_hour, self.keep_raw, self.keep_day,
                                                     self.keep_month, self.keep_year, self.keep_years)

        # Timer to read electric_meters every db_step
        schedule.every(3600/self.data_per_hour).seconds.do(self._read_electric_meters)
        schedule_thread = threading.Thread(target=_run_scheduler)
        schedule_thread.setDaemon(True)
        schedule_thread.start()

    # Electric Meter API

    def add_electric_meter(self, value, pin, active_low, name):
        self.next_id += 1

        if self.development:
            new_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            new_meter = ElectricMeter(value, pin, active_low, name)
        self.electric_meters[self.next_id] = new_meter

        # Add Datasource to Database
        self.database.add_data_src(self.next_id)

        return new_meter, self.next_id

    def remove_electric_meter(self, id):
        removed_meter = self.electric_meters[id]
        # Remove datasource
        self.database.remove_data_src(id)
        # Remove Electric meter
        del self.electric_meters[id]

        return removed_meter

    def get_electric_meter(self, id):
        return self.electric_meters[id]

    def get_electric_meters(self):
        return self.electric_meters.items()

    def change_electric_meter(self, id, value=None, pin=None, active_low=None, name=None):
        # TODO
        try:
            electric_meter = self.electric_meters[id]
        except KeyError as e:
            raise e

        if value is not None:
            electric_meter.value = value
        if pin is not None:
            electric_meter.pin = pin
        if active_low is not None:
            electric_meter.active_low = active_low
        if name is not None:
            electric_meter.name = name

        return electric_meter

    def _read_electric_meters(self):
        for id, electric_meter in self.electric_meters.items():
            value = electric_meter.get_amount()
            self.database.add_data(value, id)
            electric_meter.reset()

    # Data API
    # TODO t_minus
    def get_raw(self):
        return self.database.get_raw().items()

    def get_day(self, t_minus=0):
        data = self.database.get_day().items()

        return data

    def get_week(self, t_minus=0):
        # TODO
        data = self.database.get_month().items()

        return data

    def get_month(self, t_minus=0):
        return self.database.get_month()

    def get_year(self, t_minus=0):
        return self.database.get_year()

    def get_years(self):
        return self.database.get_years()
    # TODO
