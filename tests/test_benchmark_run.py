import unittest
import json
import testfixtures
import logging

from src.benchmark_run import SpecJBBRun, TopologyConfiguration, InvalidRunConfigurationException

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
            "jar": "/path/to/jar",
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

class TestTopologyConfiguration(unittest.TestCase):
    valid_props = [
            {
		    "backends": 2,
		    "injectors": 4,
		    "controller": ["arg1", "arg2"],
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },
            {
		    "backends": {
                        "count": 2,
                        "options": ["arg1", "arg2"],
                        },
		    "injectors": 4,
		    "controller": ["arg1", "arg2"],
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },
            {
		    "backends": 2,
		    "injectors": {
                        "count": 4,
                        "options": ["arg1", "arg2"],
                        },
		    "controller": ["arg1", "arg2"],
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },
            {
		    "backends": 2,
		    "injectors": 4,
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },
            {
		    "backends": 2,
		    "injectors": 4,
		    "jvm": {
                        "path": "java",
                        "options": ["any", "options"],
                        },
		    "jar": "env/Main.jar",
                },
            ]

    invalid_props = [
            {
		    "injectors": 4,
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },
            {
		    "backends": 4,
		    "jvm": "java",
		    "jar": "env/Main.jar"
                },

            ]
    def test_valid_props_work(self):
        for valid in self.valid_props:
            TopologyConfiguration(**valid)

    def test_invalid_props_dont_work(self):
        for invalid in self.invalid_props:
            with self.assertRaises(Exception):
                TopologyConfiguration(**invalid)

    def test_valid_give_run_options(self):
        t = TopologyConfiguration(**{
            "backends": 2,
            "injectors": 4,
            "jvm": "java",
            "jar": "env/Main.jar",
                })

        for f in [t.controller_run_args, t.backend_run_args, t.injector_run_args]:
            self.assertTrue("env/Main.jar" in f())
            self.assertTrue("java" in f())
            self.assertEqual("java", f()[0])

