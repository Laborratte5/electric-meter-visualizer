from ElectricMeter import ElectricMeter
from ElectricMeterMockup import ElectricMeterMockup


class Logic:

    def __init__(self, development):
        self.development = development
        self.next_id = 0  # TODO letzte id aus datei laden
        self.electric_meters = {}  # TODO aus datei laden
        pass

    def add_electric_meter(self, value, pin, active_low, name):
        self.next_id += 1

        if self.development:
            new_meter = ElectricMeterMockup(value, pin, active_low, name)
        else:
            new_meter = ElectricMeter(value, pin, active_low, name)
        self.electric_meters[self.next_id] = new_meter

        # TODO timer um alle 'intervall' amount von electric-meter auszulesen

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
