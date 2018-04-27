import unittest
import json
import testfixtures
import logging

from src.benchmark_run import SpecJBBRun, InvalidRunConfigurationException

class TestBenchmarkRun(unittest.TestCase):
    valid_props = [
            { # multijvm run with counts for each
                "backends": 2,
                "injectors": 4,
                "controller": {
                    "type": "multi",
                    "options": ["arg1", "arg2"],
                    },
                "java": "java",
                "jar": "env/Main.jar",
                },
            { # composite run with arguments
                "controller": {
                    "type": "composite",
                    "options": ["arg1", "arg2"],
                    },
                "java": "java",
                "jar": "env/Main.jar",
                },
            ]

    invalid_props = [
            {
                "injectors": 4,
                "java": "java",
                "jar": "env/Main.jar"
                },
            {
                "backends": 4,
                "java": "java",
                "jar": "env/Main.jar"
                },
            ]

    def test_valid_props_work(self):
        for valid in self.valid_props:
            SpecJBBRun(**valid)

    def test_invalid_props_dont_work(self):
        for invalid in self.invalid_props:
            with self.assertRaises(Exception):
                SpecJBBRun(**invalid)

    def test_valid_give_run_options(self):
        t = SpecJBBRun(**{
            "backends": 2,
            "injectors": 4,
            "controller": {
                "type": "multi",
                "options": ["arg1", "arg2"],
                },
            "java": "java",
            "jar": "env/Main.jar",
            })

        for f in [t.controller_run_args, t.backend_run_args, t.injector_run_args]:
            self.assertTrue("env/Main.jar" in f())
            self.assertTrue("java" in f())
            self.assertEqual("java", f()[0])


    def test_run_with_empty_config_gives_exception(self):
        with self.assertRaises(InvalidRunConfigurationException):
            r = SpecJBBRun()

    def test_valid_run_can_dump_info(self):
        for valid in self.valid_props:
            r = SpecJBBRun(**valid)
            with testfixtures.LogCapture() as l:
                r.dump()
                # need to have some actual logging output
                self.assertTrue(l.actual())
