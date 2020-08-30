class ElectricMeter():

    def __init__(self, value):
        self.value = value
        self.count = 0
        # TODO pin interrupts
        pass

    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = 0