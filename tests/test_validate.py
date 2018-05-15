from schema import SchemaError
from unittest import TestCase
import json
from src.validate import validate, TemplateSchema


class TestSpectateConfigValidator(TestCase):

    def test_example_config_does_validate(self):
        with open('example_config.json') as f:
            j = json.loads(f.read())
            self.assertTrue(validate(j))

    def test_invalid_config_does_not_validate(self):
        with self.assertRaises(Exception):
            with open('tests/fixtures/sample_config_invalid.json') as f:
                j = json.loads(f.read())
                self.assertFalse(validate(j))

    def test_TemplateData_with_extra_translations_dont_validate(self):
        with self.assertRaises(Exception):
            validate({
                "TemplateData": {
                    "example": {
                        "args": [],
                        "translations": {
                            "arg1": "someValue",
                        },
                    },
                },
                "RunList": [],
            })

    def test_there_should_be_TemplateData_if_there_are_RunList(self):
        with self.assertRaises(Exception):
            self.assertFalse(
                validate({
                    "TemplateData": {},
                    "RunList": [{
                        "template_type": "NONE",
                        "args": {
                            "a": "b"
                        },
                    }],
                }))

    def test_RunList_with_extra_args_fail_to_validate(self):
        with self.assertRaises(Exception):
            validate({
                "TemplateData": {
                    "example": {
                        "args": [],
                        "translations": {
                            "arg1": "someValue",
                        },
                    },
                },
                "RunList": [{
                    "template_type": "example",
                    "args": {
                        "a": "b",
                        "arg1": 5,
                    },
                }],
            })

    def test_RunList_with_ommitted_with_no_defaults_fail_to_validate(self):
        with self.assertRaises(Exception):
            validate({
                "TemplateData": {
                    "example": {
                        "args": [
                            "arg1",
                            "noDefaults",
                        ],
                        "translations": {
                            "arg1": "someValue",
                        },
                        "prop_options": {
                            "arg1": "defaultvalue",
                        },
                    },
                },
                "RunList": [{
                    "template_type": "example",
                    "args": {
                        "arg1": 5,
                    },
                }],
            })

    def test_RunList_with_extra_annotations_fail_to_validate(self):
        with self.assertRaises(Exception):
            validate({
                "TemplateData": {
                    "example": {
                        "args": [
                            "arg1",
                        ],
                        "annotations": {
                            "arg1": "someValue",
                            "extraAnnotation": "someValue",
                        },
                    },
                },
                "RunList": []
            })

    def test_RunList_with_times_validates(self):
        sample_args = {
            "Tag": "sample Tag",
            "Kit Version": "kitVer",
            "JDK": "jdk1.9",
            "RTSTART": 2,
            "JVM Options": "",
            "NUMA Nodes": 4,
            "Data Collection": "",
            "T1": 1,
            "T2": 2,
            "T3": 3,
        }

        v = validate({
                "TemplateData": {
                    "HBIR": {
                        "args": [
                            "Tag", "Kit Version", "JDK", "RTSTART",
                            "JVM Options", "NUMA Nodes", "Data Collection",
                            "T1", "T2", "T3"
                        ],
                        "prop_options": {
                            "specjbb.controller.type": "HBIR",
                            "specjbb.time.server": False,
                            "specjbb.comm.connect.client.pool.size": 192,
                            "specjbb.comm.connect.selector.runner.count": 4,
                            "specjbb.comm.connect.timeouts.connect": 650000,
                            "specjbb.comm.connect.timeouts.read": 650000,
                            "specjbb.comm.connect.timeouts.write": 650000,
                            "specjbb.comm.connect.worker.pool.max": 320,
                            "specjbb.customerDriver.threads": 64,
                            "specjbb.customerDriver.threads.saturate": 144,
                            "specjbb.customerDriver.threads.probe": 96,
                            "specjbb.mapreducer.pool.size": 27
                        },
                        "translations": {
                            "RTSTART": "specjbb.controller.rtcurve.start",
                            "T1": "specjbb.forkjoin.workers.Tier1",
                            "T2": "specjbb.forkjoin.workers.Tier2",
                            "T3": "specjbb.forkjoin.workers.Tier3",
                            "NUMA Nodes": "specjbb.group.count"
                        }
                    },
                },
                "RunList": [
                    {
                        "template_type": "HBIR",
                        "args": sample_args,
                    },
                    {
                        "template_type": "HBIR",
                        "args": sample_args,
                        "times": 2,
                    },
                ]
            })

        for run in v["RunList"]:
            self.assertEqual(sample_args, run["args"])

        self.assertEqual(v["RunList"][0]["times"], 1)
        self.assertEqual(v["RunList"][1]["times"], 2)
