import unittest
import os

import ConfigLoader
from ConfigLoader import Config


def cleanup() -> None:
    if os.path.exists(ConfigLoader.CONFIG_FILE):
        os.remove(ConfigLoader.CONFIG_FILE)


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.isfile(ConfigLoader.CONFIG_FILE):
            os.remove(ConfigLoader.CONFIG_FILE)

        Config.config = None
        Config.config_parser = None
        self.addCleanup(cleanup)

    def test_load_missing_config(self):
        # Should return default config
        # And create config file
        config = Config.get_config()

        # Assert default config
        self.assertEqual('database.json', config.get_database_file())
        self.assertEqual(4, config.get_data_per_hour())
        self.assertEqual(10, config.get_keep_raw())
        self.assertEqual(48, config.get_keep_day())
        self.assertEqual(31, config.get_keep_month())
        self.assertEqual(12, config.get_keep_year())
        self.assertEqual(3, config.get_keep_years())
        # Assert config file created
        self.assertTrue(os.path.isfile(ConfigLoader.CONFIG_FILE))

    def test_load_invalid_config_file(self):
        def assert_default_config(config):
            self.assertEqual('database.json', config.get_database_file())
            self.assertEqual(4, config.get_data_per_hour())
            self.assertEqual(10, config.get_keep_raw())
            self.assertEqual(48, config.get_keep_day())
            self.assertEqual(31, config.get_keep_month())
            self.assertEqual(12, config.get_keep_year())
            self.assertEqual(3, config.get_keep_years())

        # Create invalid config file
        with open(ConfigLoader.CONFIG_FILE, 'x') as config_file:
            config_file.write('[DATABASE]\n')
            config_file.write('database-file=\n')
            config_file.write('data-per-hour=a\n')

        # Load config
        config = Config.get_config()
        # Assert default config
        assert_default_config(config)
        # Assert config file still exists
        self.assertTrue(os.path.isfile(ConfigLoader.CONFIG_FILE))

        # Assert if default config was saved to file # TODO vllt doch nicht überschreiben
        Config.config_parser = None
        Config.config = None
        config = Config.get_config()
        assert_default_config(config)

        # Assert config file still exists
        self.assertTrue(os.path.isfile(ConfigLoader.CONFIG_FILE))
        self.assertIsNotNone(config)

    def test_save_config(self):
        database_file = 'newfile.db'
        data_per_hour = 3600
        keep_raw = 1
        keep_day = 1
        keep_month = 1
        keep_year = 1
        keep_years = 1

        config = Config.get_config()
        config.database_file = database_file
        config.data_per_hour = data_per_hour
        config.keep_raw = keep_raw
        config.keep_day = keep_day
        config.keep_month = keep_month
        config.keep_year = keep_year
        config.keep_years = keep_years
        config.save_config()

        # Assertion
        with open(ConfigLoader.CONFIG_FILE) as config_file:
            config_lines = []
            for line in config_file.readlines():
                config_lines.append(line)
            self.assertIn('[DATABASE]\n', config_lines)
            self.assertIn('database-file = ' + database_file + '\n', config_lines)
            self.assertIn('data-per-hour = ' + str(data_per_hour) + '\n', config_lines)
            self.assertIn('keep-raw = ' + str(keep_raw) + '\n', config_lines)
            self.assertIn('keep-day = ' + str(keep_day) + '\n', config_lines)
            self.assertIn('keep-month = ' + str(keep_month) + '\n', config_lines)
            self.assertIn('keep-year = ' + str(keep_year) + '\n', config_lines)
            self.assertIn('keep-years = ' + str(keep_years) + '\n', config_lines)

    def test_load_config(self):
        database_file = 'save.db'
        data_per_hour = 5
        keep_raw = 7
        keep_day = 5
        keep_month = 9
        keep_year = 34
        keep_years = 0

        # Write config
        with open(ConfigLoader.CONFIG_FILE, 'w') as file:
            file.write('[DATABASE]\n')
            file.write('database-file = ' + str(database_file) + '\n')
            file.write('data-per-hour = ' + str(data_per_hour) + '\n')
            file.write('keep-raw = ' + str(keep_raw) + '\n')
            file.write('keep-day = ' + str(keep_day) + '\n')
            file.write('keep-month = ' + str(keep_month) + '\n')
            file.write('keep-year = ' + str(keep_year) + '\n')
            file.write('keep-years = ' + str(keep_years) + '\n')

        # Load config
        config = Config.get_config()

        # Assertion
        self.assertEqual(database_file, config.get_database_file())
        self.assertEqual(data_per_hour, config.get_data_per_hour())
        self.assertEqual(keep_raw, config.get_keep_raw())
        self.assertEqual(keep_day, config.get_keep_day())
        self.assertEqual(keep_month, config.get_keep_month())
        self.assertEqual(keep_year, config.get_keep_year())
        self.assertEqual(keep_years, config.get_keep_years())


if __name__ == '__main__':
    unittest.main()
