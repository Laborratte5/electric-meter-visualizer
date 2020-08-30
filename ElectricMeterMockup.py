from ElectricMeter import ElectricMeter


class ElectricMeterMockup(ElectricMeter):

    def __init__(self):
        ElectricMeter.__init__(self, 1)

    def set_count(self, new_count):
        super().count = new_count
