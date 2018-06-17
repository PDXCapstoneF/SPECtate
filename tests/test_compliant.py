import unittest
from src import compliant


class TestComplianceProps(unittest.TestCase):

    def test_defaults_are_compliant(self):
        self.assertTrue(compliant.compliant())
        self.assertTrue(compliant.compliant({}))

    def test_group_count_must_be_compliant(self):
        self.assertFalse(compliant.compliant({
            "specjbb.group.count": -1,
        }))

    def test_transaction_injector_count_must_be_compliant(self):
        self.assertFalse(
            compliant.compliant({
                "specjbb.txi.pergroup.count": -1,
            }))

    def test_mapreducer_must_be_compliant(self):
        self.assertFalse(
            compliant.compliant({
                "specjbb.mapreducer.pool.size": 1,
            }))
