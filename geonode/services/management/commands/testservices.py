from django.core.management.base import NoArgsCommand
import unittest
from geonode.services.tests import ServicesTests


class Command(NoArgsCommand):
    help = """
    """

    def handle_noargs(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(ServicesTests)
        unittest.TextTestRunner().run(suite)
