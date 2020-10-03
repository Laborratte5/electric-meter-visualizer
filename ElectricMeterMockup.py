import random


class ElectricMeterMockup:

    def __init__(self, value, pin, active_low, name):
        self.value = value
        self.pin = pin
        self.active_low = active_low
        self.name = name
        self.count = 0

    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = random.randint(0, 100)

    def set_count(self, new_count):
        self.count = new_count
