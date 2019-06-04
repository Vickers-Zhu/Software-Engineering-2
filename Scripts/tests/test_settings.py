import unittest

import env

import common.settings as settings

class SettingsTest(unittest.TestCase):

    def test_initialization(self):
        s = settings.Settings()

        self.assertEqual(type(s), settings.Settings)

    def test_settings_are_not_empty(self):
        s = settings.Settings()

        for _attr, value in s.__dict__.items():
            self.assertNotEqual(value, None)


if __name__ == '__main__':
    unittest.main(exit=False)