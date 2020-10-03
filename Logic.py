import threading
import time
from datetime import datetime, timedelta

from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup
import os
import schedule

from Database import Database
from Database import RoundRobinArchive as RRA
from Database import Datasource as DS


def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


class Logic:

    def __init__(self, development):
        self.development = development
        self.next_id = 0  # TODO letzte id aus datei laden
        self.electric_meters = {}  # TODO aus datei laden
        self.datasource_electric_meter_mapping = {}  # TODO aus datei laden
        self.datasources = []  # TODO aus datei laden
        self.config = {}  # TODO aus config laden

        self.db_step = 900  # 15min. # TODO step vllt aus config laden

        database_file = 'data.rrd'
        if os.path.isfile(database_file):
            self.database = Database.load(database_file)
        else:
            # Time/step values for rrd
            hourly = 3600 / self.db_step
            daily = 24 * hourly
            weekly = 7 * daily
            yearly = ((3 * 365 + 366) / 4) * daily
            monthly = yearly / 12

            # TODO aus config laden
            keep_steps = 96
            keep_daily = 7
            keep_weekly = 4
            keep_monthly = 12
            keep_yearly = 3

            xff = 0.5

            rras = [RRA('LAST', xff, 1, keep_steps),
                    # Average RRA
                    RRA('AVERAGE', xff, daily, keep_daily),
                    RRA('AVERAGE', xff, weekly, keep_weekly),
                    RRA('AVERAGE', xff, monthly, keep_monthly),
                    RRA('AVERAGE', xff, yearly, keep_yearly),
                    # Min RRA
                    RRA('MIN', xff, daily, keep_daily),
                    RRA('MIN', xff, weekly, keep_weekly),
                    RRA('MIN', xff, monthly, keep_monthly),
                    RRA('MIN', xff, yearly, keep_yearly),
                    # Max RRA
                    RRA('MAX', xff, daily, keep_daily),
                    RRA('MAX', xff, weekly, keep_weekly),
                    RRA('MAX', xff, monthly, keep_monthly),
                    RRA('MAX', xff, yearly, keep_yearly)]
            # TODO nochmal nachdenken ob so wirklich richtige gespeichert wird

            # Create Database
            dummy_data_source = DS('DUMMY', 'GAUGE', 2 * self.db_step)
            self.database = Database.create(database_file, self.db_step, dummy_data_source, rras)

        # Timer to read electric_meters every db_step
        schedule.every(self.db_step).seconds.do(self._read_electric_meters)
        schedule_thread = threading.Thread(target=_run_scheduler)
        schedule_thread.setDaemon(True)
        schedule_thread.start()
        # TODO schedule run_pending()

    # Electric Meter API

    def add_electric_meter(self, value, pin, active_low, name):
        self.next_id += 1

        if self.development:
            new_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            new_meter = ElectricMeter(value, pin, active_low, name)
        self.electric_meters[self.next_id] = new_meter

        # Add Datasource to Database
        new_datasource = DS(name, 'GAUGE', self.db_step*2, min=0)
        self.database.add_data_source(new_datasource)
        self.datasource_electric_meter_mapping[new_datasource] = new_meter
        self.datasources.append(new_datasource)

        return new_meter, self.next_id

    def remove_electric_meter(self, id):
        removed_meter = self.electric_meters[id]
        removed_datasource = None
        # Get removed datasource
        for datasource in self.datasources:
            em = self.datasource_electric_meter_mapping[datasource]
            if self.datasource_electric_meter_mapping[datasource] is removed_meter:
                removed_datasource = datasource
                break

        # Remove Datasource Mapping
        self.database.remove_data_source(removed_datasource)
        self.datasources.remove(removed_datasource)
        del self.datasource_electric_meter_mapping[removed_datasource]
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
        data_list = []
        for datasource in self.datasources:
            electric_meter = self.datasource_electric_meter_mapping[datasource]
            power_usage = electric_meter.get_amount()
            data_list.append(power_usage)
            electric_meter.reset()

        data_list.insert(0, 0)  # Insert data dummy
        # Add data_list to database
        self.database.add_data(data_list)
        pass
