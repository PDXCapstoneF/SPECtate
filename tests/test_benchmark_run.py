import unittest
import json
import testfixtures
import logging

from src.benchmark_run import SpecJBBRun, InvalidRunConfigurationException, JvmRunOptions, SpecJBBComponentOptions, SpecJBBComponentTypes


class TestBenchmarkRun(unittest.TestCase):
    valid_props = [
        {  # multijvm run with counts for each
            "backends": 2,
            "injectors": 4,
            "controller": {
                "type": "multi",
                "options": ["arg1", "arg2"],
            },
            "java": "java",
            "jar": "env/Main.jar",
        },
        {  # composite run with arguments
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
            self.assertTrue(any("env/Main.jar" in arg for arg in f()))
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


class TestJvmRunOptions(unittest.TestCase):
    def test_given_none_will_fill_defaults(self):
        self.assertTrue(JvmRunOptions())

    def test_given_str(self):
        java_path = "java"
        j = JvmRunOptions(java_path)

        self.assertEqual(j.path, java_path)
        self.assertEqual(j["path"], java_path)
        self.assertEqual(j.options, [])
        self.assertEqual(j["options"], [])

    def test_given_list(self):
        java_list = ["java", "-jar", "example_jar"]
        j = JvmRunOptions(java_list)

        self.assertEqual(j.path, java_list[0])
        self.assertEqual(j["path"], java_list[0])
        self.assertEqual(j.options, java_list[1:])
        self.assertEqual(j["options"], java_list[1:])

    def test_given_dict(self):
        valid = {
            "path": "java",
            "options": ["-jar", "example_jar"],
        }

        j = JvmRunOptions(valid)

        self.assertEqual(j.path, valid["path"])
        self.assertEqual(j["path"], valid["path"])
        self.assertEqual(j.options, valid["options"])
        self.assertEqual(j["options"], valid["options"])

    def test_with_dict_missing_options(self):
        valid = {
            "path": "java",
        }

        j = JvmRunOptions(valid)

        self.assertEqual(j.path, valid["path"])
        self.assertEqual(j["path"], valid["path"])
        self.assertEqual(j.options, [])
        self.assertEqual(j["options"], [])

    def test_validates_dictionaries(self):
        invalid_missing_path = {
            "options": []
        }

        with self.assertRaises(Exception):
            j = JvmRunOptions(invalid_missing_path)

        invalid_types = {
            "path": 2,
            "options": {}
        }

        with self.assertRaises(Exception):
            j = JvmRunOptions(invalid_types)


class TestSpecJBBComponentOptions(unittest.TestCase):
    def test_given_invalid_type(self):
        with self.assertRaises(Exception):
            SpecJBBComponentOptions("foo")

    def test_given_none(self):
        component_options = list(
            map(lambda c: SpecJBBComponentOptions(c), SpecJBBComponentTypes))

        for co in component_options:
            self.assertEqual(co["count"], 1)
            self.assertEqual(co["options"], [])
            self.assertEqual(co["jvm_opts"], [])

    def test_given_int(self):
        count = 5
        component_options = list(
            map(lambda c: SpecJBBComponentOptions(c, count), SpecJBBComponentTypes))

        for co in component_options:
            self.assertEqual(co["count"], count)
            self.assertEqual(co["options"], [])
            self.assertEqual(co["jvm_opts"], [])

    def test_given_dict(self):
        options = ["a", "b"]
        jvm_opts = ["c", "d"]

        component_options = list(map(lambda c: SpecJBBComponentOptions(c, {
            "options": options,
            "jvm_opts": jvm_opts,
        }), SpecJBBComponentTypes))

        for co in component_options:
            self.assertEqual(co["count"], 1)
            self.assertEqual(co["options"], options)
            self.assertEqual(co["jvm_opts"], jvm_opts)
