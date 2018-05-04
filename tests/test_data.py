import unittest

from src import objects
from src import data

class TestData(unittest.TestCase):
    def test_get_defaults_returns_list(self):
        self.assertTrue(data.DataLoader.defaults())

    def test_get_defaults_returns_same_as_objects_defaults(self):
        od = objects.defaults
        df = data.DataLoader.defaults()

        self.assertEqual(od, df)

