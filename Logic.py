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

    def get_electric_meter(self):
        return [(self.electric_meters[id], id) for id in self.electric_meters.keys()]
