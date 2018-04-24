from schema import SchemaError
from unittest import TestCase
import json
from src.validate import validate, validate_blackbox

class TestConfigValidator(TestCase):
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

    def test_example_spectate_config_does_validate(self):
        with open('example_spectate_config.json') as f:
            j = json.loads(f.read())
            self.assertTrue(validate(j))

    def test_invalid_spectate_config_does_not_validate(self):
        with self.assertRaises(Exception):
            with open('tests/fixtures/sample_spectate_config_invalid.json') as f:
                j = json.loads(f.read())
                self.assertFalse(validate(j))

