import unittest

from src import distributed


class TestGetHostname(unittest.TestCase):
    def test_get_hostname_does_localhost(self):
        self.assertEqual(distributed.get_hostname("localhost"), "localhost")

    def test_get_hostname_does_ips(self):
        self.assertEqual(distributed.get_hostname("127.0.0.1"), "127.0.0.1")

    def test_get_hostname_strips_ports(self):
        self.assertEqual(distributed.get_hostname("localhost:80"), "localhost")

    def test_get_hostname_does_ips_with_ports(self):
        self.assertEqual(distributed.get_hostname("127.0.0.1:80"), "127.0.0.1")

class TestToPair(unittest.TestCase):
    def test_to_pair_always_returns_something(self):
        p = distributed.to_pair(("specjbb.property.name", 2))
        self.assertTrue(p)

class TestDistributedComponent(unittest.TestCase):
    def test_host_required_for_distributed_component(self):
        with self.assertRaises(Exception):
            distributed.DistributedComponent(meta={}, component={"a": 2})

