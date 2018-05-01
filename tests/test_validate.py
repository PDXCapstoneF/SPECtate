from schema import SchemaError
from unittest import TestCase
import json
from src.validate import validate, validate_blackbox, TemplateSchema

class TestBlackboxConfigValidator(TestCase):
    def test_empty_config_does_not_validate(self):
        with self.assertRaises(SchemaError):
            validate({})

    def test_example_config_does_validate(self):
        with open('example_config.json') as f:
            j = json.loads(f.read())
            self.assertTrue(validate_blackbox(j))

    def test_invalid_config_does_not_validate(self):
        with self.assertRaises(SchemaError):
            with open('tests/fixtures/sample_config_invalid.json') as f:
                j = json.loads(f.read())
                self.assertFalse(validate(j))

class TestSpectateConfigValidator(TestCase):
    def test_example_spectate_config_does_validate(self):
        with open('example_spectate_config.json') as f:
            j = json.loads(f.read())
            self.assertTrue(validate(j))

    def test_invalid_spectate_config_does_not_validate(self):
        with self.assertRaises(Exception):
            with open('tests/fixtures/sample_spectate_config_invalid.json') as f:
                j = json.loads(f.read())
                self.assertFalse(validate(j))

    def test_templates_with_extra_translations_dont_validate(self):
        self.assertFalse(validate({
            "templates": {
                "example": {
                    "args": [],
                    "translations": { 
                        "arg1": "someValue",
                        },
                    },
                },
            "runs": [],
            }))

    def test_there_should_be_templates_if_there_are_runs(self):
        with self.assertRaises(Exception):
            self.assertFalse(validate({
                "templates": {},
                "runs": [
                    {
                        "template_name": "NONE",
                        "args": { "a": "b" },
                        }
                    ],
                }))

    def test_runs_with_extra_args_fail_to_validate(self):
        self.assertFalse(validate({
            "templates": {
                "example": {
                    "args": [],
                    "translations": { 
                        "arg1": "someValue",
                        },
                    },
                },
            "runs": [
                {
                    "template_name": "example",
                    "args": {
                        "a": "b",
                        "arg1": 5,
                        },
                    }
                ],
            }))

    def test_runs_with_ommitted_with_no_defaults_fail_to_validate(self):
        self.assertFalse(validate({
            "templates": {
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
            "runs": [
                {
                    "template_name": "example",
                    "args": {
                        "arg1": 5,
                        },
                    }
                ],
            }))

    def test_runs_with_extra_annotations_fail_to_validate(self):
        self.assertFalse(validate({
            "templates": {
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
            "runs": []
            }))
