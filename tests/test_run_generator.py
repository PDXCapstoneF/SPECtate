import json
import unittest
import src.run_generator

class TestRunGenerator(unittest.TestCase):
    """
    Test cases for a run generator that takes validated tate configs
    and translates them into objects that SpecJBBRun can consume.
    """
    def test_run_generator_generates_valid_RunList_with_example(self):
        with open("example_spectate_config.json", 'r') as f:
            c = json.loads(f.read())

        rg = src.run_generator.RunGenerator(**c)

        for run in rg.runs:
            self.assertTrue(run)

