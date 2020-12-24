
STATE_FILE = 'state.json'


class State:

    @classmethod
    def get_state(cls):
        pass

    def save_state(self):
        pass

    def get_next_id(self):
        pass

    def set_next_id(self, next_id):
        pass

    def get_electric_meters(self):
        pass

    def set_electric_meters(self, electric_meters):
        pass


class InvalidStateFileException(Exception):
    pass
