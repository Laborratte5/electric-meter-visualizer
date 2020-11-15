import unittest
import os

import ConfigLoader
from ConfigLoader import Config


def cleanup() -> None:
    if os.path.exists(ConfigLoader.CONFIG_FILE):
        os.remove(ConfigLoader.CONFIG_FILE)


class MyTestCase(unittest.TestCase):
    # TODO load invalie config
    # TODO load config

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
        # Create invalid config file
        with open(ConfigLoader.CONFIG_FILE, 'x') as config_file:
            config_file.write('[DATABASE]\n')
            config_file.write('database-file=\n')
            config_file.write('data-per-hour=a\n')

        # Load config
        config = Config.get_config()
        # Assertion
        # TODO
        self.assertIsNotNone(config)

    def test_save_config(self):
        config = Config.get_config()
        config.database_file = 'newfile.db'
        config.data_per_hour = 3600
        config.keep_raw = 1
        config.keep_day = 1
        config.keep_month = 1
        config.keep_year = 1
        config.keep_years = 1
        config.save_config()

        # Assertion
        with open(ConfigLoader.CONFIG_FILE) as config_file:
            config_lines = []
            for line in config_file.readlines():
                config_lines.append(line)
            self.assertIn('database-file = newfile.db\n', config_lines)
            self.assertIn('data-per-hour = 3600\n', config_lines)
            self.assertIn('keep-raw = 1\n', config_lines)
            self.assertIn('keep-day = 1\n', config_lines)
            self.assertIn('keep-month = 1\n', config_lines)
            self.assertIn('keep-year = 1\n', config_lines)
            self.assertIn('keep-years = 1\n', config_lines)

    def test_load_config(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
