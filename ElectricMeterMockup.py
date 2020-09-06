
class ElectricMeterMockup:

    def __init__(self, value, pin, active_low, name):
        print('new electric meter with: ', value, pin, active_low, name)
        self.value = value
        self.pin = pin
        self.active_low = active_low
        self.name = name
        self.count = 0
        # TODO pin interrupts
        pass

    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = 0

    def set_count(self, new_count):
        super().count = new_count
