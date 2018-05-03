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
        self.assertFalse(validate({
            "TemplateData": {
                "example": {
                    "args": [],
                    "translations": { 
                        "arg1": "someValue",
                        },
                    },
                },
            "RunList": [],
            }))

    def test_there_should_be_TemplateData_if_there_are_RunList(self):
        with self.assertRaises(Exception):
            self.assertFalse(validate({
                "TemplateData": {},
                "RunList": [
                    {
                        "template_type": "NONE",
                        "args": { "a": "b" },
                        }
                    ],
                }))

    def test_RunList_with_extra_args_fail_to_validate(self):
        self.assertFalse(validate({
            "TemplateData": {
                "example": {
                    "args": [],
                    "translations": { 
                        "arg1": "someValue",
                        },
                    },
                },
            "RunList": [
                {
                    "template_type": "example",
                    "args": {
                        "a": "b",
                        "arg1": 5,
                        },
                    }
                ],
            }))

    def test_RunList_with_ommitted_with_no_defaults_fail_to_validate(self):
        self.assertFalse(validate({
            "TemplateData": {
                "example": {
                    "args": [
                        "arg1",
                        "noDefaults",
                        ],
                    "translations": { 
                        "arg1": "someValue",
                        },
                "default_props": {
                    "arg1": "defaultvalue",
                    },
                },
            },
            "RunList": [
                {
                    "template_type": "example",
                    "args": {
                        "arg1": 5,
                        },
                    }
                ],
            }))

    def test_RunList_with_extra_annotations_fail_to_validate(self):
        self.assertFalse(validate({
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
            }))

    def test_runs_with_template_as_filename(self):
        self.assertTrue(validate({
            "templates": {
                "PRESET": "templates/PRESET_template.json",
                "HBIR_RT": "templates/HBIR_RT_template.json",
                "LOADLEVELS": "templates/LOADLEVELS_template.json",
                },
            "runs": [],
            }))
