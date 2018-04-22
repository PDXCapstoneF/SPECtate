import unittest

from src.task_runner import TaskRunner

class TestTaskRunner(unittest.TestCase):
    valid_options = [
            "echo",
            "hello",
            "world",
            ]

    invalid_options = [
            [ # given non-string arguments
                "echo",
                2,
                None,
                False,
                ],
            ]

    def test_init_with_valid_options_works(self):
        TaskRunner(self.valid_options)

    def test_init_with_invalid_options_fails(self):
        with self.assertRaises(Exception):
            for invalid in self.invalid_options:
                TaskRunner(*invalid)

    def test_run_actually_runs(self):
        t = TaskRunner("echo", "hello", "world")
        t.run()

    def test_run_with_list_in_arg_is_unpacked(self):
        t = TaskRunner("echo", ["hello", "world"], "this", "should", "be unpacked")
        t.run()

