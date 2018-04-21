import unittest
import json
import testfixtures
import logging

from src.benchmark_run import SpecJBBRun, InvalidRunConfigurationException

class TestBenchmarkRun(unittest.TestCase):
    valid_props = {
        "args": [
            "Arg1",
            "Arg2",
            ],
        "annotations": {
            "Arg1": "This is the first argument",
            "Arg2": "This is the second argument",
            },
        "types": {
            "Arg1": "string",
            "Arg2": "int",
            },
        "translations": {
            "Arg1": "com.spec.prop1",
            },
        "default_props": {},
        }

    valid_tate_props = {
            "backends": 2,
            "injectors": 14,
            "jvm": {
                "path": "/path/to/jvm",
                "options": [], # to be condensed into a string later
            },
            "specjbb": {
                "jar": "/path/to/jar",
            },
        }

    def test_run_with_empty_config_gives_exception(self):
        with self.assertRaises(InvalidRunConfigurationException):
            r = SpecJBBRun()

    def test_run_with_valid_configuration(self):
        SpecJBBRun(props=self.valid_tate_props, **self.valid_props)

    def test_valid_run_can_dump_info(self):
        r = SpecJBBRun(props=self.valid_tate_props, **self.valid_props)
        with testfixtures.LogCapture() as l:
            r.dump()
            # need to have some actual logging output
            self.assertTrue(l.actual())

