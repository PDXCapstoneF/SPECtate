import unittest

from src import objects
from src import data

class TestData(unittest.TestCase):
    def test_get_defaults_returns_list(self):
        self.assertTrue(data.DataLoader.defaults())

    def test_get_defaults_returns_same_as_objects_defaults(self):
        # what key do we sort on?
        k = lambda p: p.prop

        # sort them both
        od = objects.defaults
        od.sort(key=k)
        df = data.DataLoader.defaults()
        df.sort(key=k)

        self.assertTrue(od)
        self.assertTrue(df)
        # they should be the same
        self.assertEqual(len(od), len(df))

