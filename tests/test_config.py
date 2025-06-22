import unittest

from webloginbrute.config import Config, ConfigurationError


class TestConfig(unittest.TestCase):
    def test_missing_required_config(self):
        with self.assertRaises(ConfigurationError):
            Config.parse_obj({})


if __name__ == "__main__":
    unittest.main()
