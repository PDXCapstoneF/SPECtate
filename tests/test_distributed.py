import unittest

from src.distributed import get_hostname

class TestGetHostname(unittest.TestCase):
    def get_hostname_does_localhost(self):
        self.assertEqual(get_hostname("localhost"), "localhost")

    def get_hostname_does_ips(self):
        self.assertEqual(get_hostname("127.0.0.1"), "127.0.0.1")

    def get_hostname_strips_ports(self):
        self.assertEqual(get_hostname("localhost:80"), "localhost")

    def get_hostname_does_ips_with_ports(self):
        self.assertEqual(get_hostname("127.0.0.1:80"), "127.0.0.1")

