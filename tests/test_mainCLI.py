import unittest
import json

import mainCLI as main

example_configuration = json.loads(open("example_config.json", "r").read())["specjbb"]

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
