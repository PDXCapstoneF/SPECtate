import unittest

from src.task_runner import TaskRunner

class TestTaskRunner(unittest.TestCase):
    valid_exec = {
            'path': '/some/path',
            'options': []
            },

    valid_options = [
            valid_exec,
            ]

    invalid_options = [
            [ # missing path
                {
                    'options': []
                    },
                ],
            [ # missing options
                {
                    'path': '/some/path'
                    },
                ],
            [ # given non-string arguments
                valid_exec,
                2,
                None,
                False,
                ],
            ]

    def test_init_with_valid_options_works(self):
        TaskRunner(*self.valid_options)

    def test_init_with_invalid_options_fails(self):
        with self.assertRaises(Exception):
            for invalid in self.invalid_options:
                TaskRunner(*invalid)

