import threading
import time

from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup
import os
import schedule

from Database import Database
from Persistence import State


def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


class Logic:

    def __init__(self, config, development):
        self.development = development
        self.state = State.get_state()

        database_file = config.get_database_file()
        self.data_per_hour = config.get_data_per_hour()

        if os.path.isfile(database_file):
            self.database = Database.load_database(database_file)
        else:
            self.keep_raw = config.get_keep_raw()
            self.keep_day = config.get_keep_day()
            self.keep_month = config.get_keep_month()
            self.keep_year = config.get_keep_year()
            self.keep_years = config.get_keep_years()
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
        next_id = self.state.get_next_id()
        electric_meters = self.state.get_electric_meters()
        self.state.set_next_id(next_id + 1)

        if self.development:
            new_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            new_meter = ElectricMeter(value, pin, active_low, name)

        electric_meters[next_id] = new_meter
        self.state.set_electric_meters(electric_meters)

        # Add Datasource to Database
        self.database.add_data_src(next_id)

        return new_meter, next_id

    def remove_electric_meter(self, id):
        removed_meter = self.state.get_electric_meters()[id]
        # Remove datasource
        self.database.remove_data_src(id)
        # Remove Electric meter
        del self.state.get_electric_meters()[id]

        return removed_meter

    def get_electric_meter(self, id):
        return self.state.get_electric_meters()[id]

    def get_electric_meters(self):
        return self.state.get_electric_meters().items()

    def change_electric_meter(self, id, value=None, pin=None, active_low=None, name=None):
        electric_meter = self.state.get_electric_meters()[id]

        if (value is None or value == electric_meter.value) \
                and (pin is None or pin == electric_meter.pin) \
                and (active_low is None or active_low == electric_meter.active_low) \
                and (name is None or name == electric_meter.name):
            return None

        if value is not None:
            electric_meter.set_value(value)
        if pin is not None:
            electric_meter.set_pin(pin)
        if active_low is not None:
            electric_meter.set_active_low(active_low)
        if name is not None:
            electric_meter.set_name(name)

        return electric_meter

    def _read_electric_meters(self):
        for id, electric_meter in self.state.get_electric_meters().items():
            value = electric_meter.get_amount()
            self.database.add_data(value, id)
            electric_meter.reset()

    # Data API
    def get_raw(self, since=None, until=None):
        data = []
        for meter_id, electric_meter in self.get_electric_meters():
            data.append(ElectricMeterData(meter_id, electric_meter,
                                          {datasource: data
                                           for datasource, data
                                           in self.database.get_raw(since=since, until=until).items()}))
        return data

    def get_day(self, since=None, until=None):
        data = []
        for meter_id, electric_meter in self.get_electric_meters():
            data.append(ElectricMeterData(meter_id, electric_meter,
                                          {datasource: data
                                           for datasource, data
                                           in self.database.get_day(since=since, until=until).items()}))
        return data

    def get_month(self, since=None, until=None):
        data = []
        for meter_id, electric_meter in self.get_electric_meters():
            data.append(ElectricMeterData(meter_id, electric_meter,
                                          {datasource: data
                                           for datasource, data
                                           in self.database.get_month(since=since, until=until).items()}))
        return data

    def get_year(self, since=None, until=None):
        data = []
        for meter_id, electric_meter in self.get_electric_meters():
            data.append(ElectricMeterData(meter_id, electric_meter,
                                          {datasource: data
                                           for datasource, data
                                           in self.database.get_year(since=since, until=until).items()}))
        return data


    def get_years(self, since=None, until=None):
        data = []
        for meter_id, electric_meter in self.get_electric_meters():
            data.append(ElectricMeterData(meter_id, electric_meter,
                                          {datasource: data
                                           for datasource, data
                                           in self.database.get_years(since=since, until=until).items()}))
        return data


class ElectricMeterData:

    def __init__(self, meter_id, electric_meter, data):
        self.id = meter_id
        self.value = electric_meter.value
        self.pin = electric_meter.pin
        self.active_low = electric_meter.active_low
        self.name = electric_meter.name
        self.data = data[meter_id]
