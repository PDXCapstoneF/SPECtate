import unittest
import json

from src.benchmark_run import SpecJBBRun, InvalidRunConfigurationException

class TestBenchmarkRun(unittest.TestCase):
    def test_run_with_empty_config_gives_exception(self):
        with self.assertRaises(InvalidRunConfigurationException):
            r = SpecJBBRun()
