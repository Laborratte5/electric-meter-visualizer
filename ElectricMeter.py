class ElectricMeter:

    def __init__(self, value, pin, active_low, name):
        self.count = 0
        self.value = None
        self.pin = None
        self.active_low = None
        self.name = None

        self.set_value(value)
        self.set_pin(pin)
        self.set_active_low(active_low)
        self.set_name(name)

        # TODO pin interrupts
        pass

    # Setter
    def set_value(self, value):
        if value <= 0:
            raise ValueError('Electric meter value must be greater than 0')
        self.value = value

    def set_pin(self, pin):
        if not 0 <= pin <= 27:
            raise ValueError('Electric meter pin out of range')
        self.pin = pin

    def set_active_low(self, active_low):
        self.active_low = active_low

    def set_name(self, name):
        if name == ' ': # TODO richtig auf whitespaces prüfen
            raise ValueError('Electric meter name must not be empty')
        self.name = name

    # Electric Meter methods
    def get_amount(self):
        return self.count * self.value

    def reset(self):
        self.count = 0
