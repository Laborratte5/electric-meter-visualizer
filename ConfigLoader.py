import os
from configparser import ConfigParser

CONFIG_FILE = 'config.ini'


class Config:

    config = None
    config_parser = None

    @classmethod
    def get_config(cls):
        if cls.config is None:
            if os.path.exists(CONFIG_FILE):
                # Load config from file
                config_parser = ConfigParser()
                config_parser.read(CONFIG_FILE)
                # Create Config object
                config = Config(config_parser)
                try:
                    config.database_file = str(config_parser['DATABASE']['database-file'])
                    config.data_per_hour = int(config_parser['DATABASE']['data-per-hour'])
                    config.keep_raw = int(config_parser['DATABASE']['keep-raw'])
                    config.keep_day = int(config_parser['DATABASE']['keep-day'])
                    config.keep_month = int(config_parser['DATABASE']['keep-month'])
                    config.keep_year = int(config_parser['DATABASE']['keep-year'])
                    config.keep_years = int(config_parser['DATABASE']['keep-years'])
                except (KeyError, ValueError) as e:
                    # Create default config
                    config = Config(config_parser)
                    # TODO print error
            else:
                # Create default config
                config_parser = ConfigParser()
                config = Config(config_parser)
                config.save_config()

            cls.config_parser = config_parser
            cls.config = config

        return cls.config

    def save_config(self):
        self.config_parser['DATABASE'] = {
            'database-file': self.get_database_file(),
            'data-per-hour': self.get_data_per_hour(),
            'keep-raw': self.get_keep_raw(),
            'keep-day': self.get_keep_day(),
            'keep-month': self.get_keep_month(),
            'keep-year': self.get_keep_year(),
            'keep-years': self.get_keep_years()
        }

        with open(CONFIG_FILE, 'w') as file:
            self.config_parser.write(file)

    def __init__(self, config_parser):
        self.config_parser = config_parser

        self.database_file = 'database.json'
        self.data_per_hour = 4
        self.keep_raw = 10
        self.keep_day = 48
        self.keep_month = 31
        self.keep_year = 12
        self.keep_years = 3

    # TODO implement config
    def get_database_file(self):
        return self.database_file

    def get_data_per_hour(self):
        return self.data_per_hour

    def get_keep_raw(self):
        return self.keep_raw

    def get_keep_day(self):
        return self.keep_day

    def get_keep_month(self):
        return self.keep_month

    def get_keep_year(self):
        return self.keep_year

    def get_keep_years(self):
        return self.keep_years
