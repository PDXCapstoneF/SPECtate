import unittest
import json
import testfixtures
import logging

from src.benchmark_run import SpecJBBRun, InvalidRunConfigurationException

class TestBenchmarkRun(unittest.TestCase):
    valid_types = {
        "args": [],
        "annotations": {},
        "types": {},
        "translations": {},
        "props": {}
        }

    valid_tate_props = {
            "backends": 2,
            "injectors": 14,
            "jvm": {
                "path": "/path/to/jvm",
                "options": [], # to be condensed into a string later
            }
        }

    def test_run_with_empty_config_gives_exception(self):
        with self.assertRaises(InvalidRunConfigurationException):
            r = SpecJBBRun()

    def test_run_with_valid_configuration(self):
        try:
            r = SpecJBBRun(types=self.valid_types, props=self.valid_tate_props)
        except Exception as e:
            self.fail(e)

    def test_valid_run_can_dump_info(self):
        try:
            r = SpecJBBRun(types=self.valid_types, props=self.valid_tate_props)
        except Exception as e:
            self.fail(e)
        with testfixtures.LogCapture() as l:
            r.dump()
            # need to have some actual logging output
            self.assertTrue(l.actual())

