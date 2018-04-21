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

    def test_run_does_stuff(self):
        t = TaskRunner("echo", "hello", "world")
        t.run()

