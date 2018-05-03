import unittest
import json

import mainCLI as main

example_config = json.loads(open("example_config.json", "r").read())

if "specjbb" not in example_config:
    raise Exception("expected specjbb to be in the example - either update this test or fix the example!")

example_configuration = example_config["specjbb"]

class TestMain(unittest.TestCase):
    def test_to_list_gives_arguments(self):
        self.assertIsNotNone(main.to_list(example_configuration))

    def test_to_list_changes_based_on_run_type(self):
        different = example_configuration.copy()
        different.update({ "run_type": "HBIR_RT" })

        if example_configuration == different:
            self.skipTest()

        self.assertNotEqual(main.to_list(example_configuration),
                main.to_list(different))
    
    def test_to_list_has_required_keys(self):
        with self.assertRaises(Exception):
            main.to_list({})
