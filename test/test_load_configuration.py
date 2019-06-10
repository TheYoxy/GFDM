from unittest import TestCase

from devops.configuration.loader import load_configuration


class Test_load_configuration(TestCase):
    def test_load_configuration(self):
        auth = load_configuration()
        self.assertTrue(auth.authentication is not None)
        self.assertTrue(auth.project is not None)