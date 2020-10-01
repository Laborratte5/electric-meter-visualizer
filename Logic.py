from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup
import os
import schedule

from Database import Database
from Database import RoundRobinArchive as RRA
from Database import Datasource as DS


class Logic:

    def __init__(self, development):
        self.development = development
        self.next_id = 0  # TODO letzte id aus datei laden
        self.electric_meters = {}  # TODO aus datei laden
        self.config = {}  # TODO aus config laden

        database_file = 'data.rrd'
        if os.path.isfile(database_file):
            self.database = Database.load(database_file)
        else:
            # Time/step values for rrd
            self.db_step = 900 # 15min. # TODO step vllt aus config laden
            hourly = 3600 / self.db_step
            daily = 24 * hourly
            weekly = 7 * daily
            yearly = ((3 * 365 + 366) / 4) * daily
            monthly = yearly / 12

            # TODO aus config laden
            keep_daily = 7
            keep_weekly = 4
            keep_monthly = 12
            keep_yearly = 3

            xff = 0.5

            rras = []
            # TODO nochmal nachdenken ob so wirklich richtige gespeichert wird
            # Average RRA
            rras.append(RRA('LAST', xff, 1, daily))
            rras.append(RRA('AVERAGE', xff, daily, keep_daily))
            rras.append(RRA('AVERAGE', xff, weekly, keep_weekly))
            rras.append(RRA('AVERAGE', xff, monthly, keep_monthly))
            rras.append(RRA('AVERAGE', xff, yearly, keep_yearly))
            # Min RRA
            rras.append(RRA('MIN', xff, daily, keep_daily))
            rras.append(RRA('MIN', xff, weekly, keep_weekly))
            rras.append(RRA('MIN', xff, monthly, keep_monthly))
            rras.append(RRA('MIN', xff, yearly, keep_yearly))
            # Max RRA
            rras.append(RRA('MAX', xff, daily, keep_daily))
            rras.append(RRA('MAX', xff, weekly, keep_weekly))
            rras.append(RRA('MAX', xff, monthly, keep_monthly))
            rras.append(RRA('MAX', xff, yearly, keep_yearly))

            dummy_data_source = DS('DUMMY','GAUGE', 2 * self.db_step)
            self.database = Database.create(database_file, self.db_step, dummy_data_source, rras)

    def add_electric_meter(self, value, pin, active_low, name):
        self.next_id += 1

        if self.development:
            new_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            new_meter = ElectricMeter(value, pin, active_low, name)
        self.electric_meters[self.next_id] = new_meter

        # TODO timer um alle 'db_step' amount von electric-meter auszulesen

        return new_meter, self.next_id

    def remove_electric_meter(self, id):
        removed_meter = self.electric_meters[id]
        del self.electric_meters[id]
        return removed_meter

    def get_electric_meter(self, id):
        return self.electric_meters[id]

    def get_electric_meters(self):
        return [(self.electric_meters[id], id) for id in self.electric_meters.keys()]

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
