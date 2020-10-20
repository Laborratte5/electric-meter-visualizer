class ElectricMeter():

    def __init__(self, value, pin, active_low, name):
        self.value = value
        self.count = 0
        self.name = name
        self.pin = pin
        self.active_low = active_low

        # TODO pin interrupts
        pass

    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = 0
