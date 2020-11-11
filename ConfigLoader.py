

class ConfigLoader:
    # TODO implement config loader
    pass


class Config:

    # TODO implement config
    def get_next_id(self):
        # TODO int
        return 0

    def get_electric_meters(self):
        # TODO dict
        return {}

    def get_database_file(self):
        # TODO string
        return 'database.json'

    def get_data_per_hour(self):
        # TODO int
        return 4

    def get_keep_raw(self):
        # TODO int
        return 10

    def get_keep_day(self):
        # TODO int
        return 48

    def get_keep_month(self):
        # TODO int
        return 30

    def get_keep_year(self):
        # TODO int
        return 12

    def get_keep_years(self):
        # TODO int
        return 3
