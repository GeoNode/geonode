from django.core.management import call_command
from django.test import TestCase, TransactionTestCase


class ImporterBaseTestSupport(TestCase):
    databases = ("default", "datastore")
    multi_db = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        """
        Why manually load the fixture after the setupClass?
        Django in the setUpClass method, load the fixture in all the databases
        that are defined in the databases attribute. The problem is that the
        datastore database will contain only the dyanmic models infrastructure
        and not the whole geonode structure. So that, having the fixture as a
        attribute will raise and error
        """
        fixture = [
            "initial_data.json",
            "group_test_data.json",
            "default_oauth_apps.json",
        ]

        call_command("loaddata", *fixture, **{"verbosity": 0, "database": "default"})


class TransactionImporterBaseTestSupport(TransactionTestCase):
    databases = ("default", "datastore")
    multi_db = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        """
        Why manually load the fixture after the setupClass?
        Django in the setUpClass method, load the fixture in all the databases
        that are defined in the databases attribute. The problem is that the
        datastore database will contain only the dyanmic models infrastructure
        and not the whole geonode structure. So that, having the fixture as a
        attribute will raise and error
        """
        fixture = [
            "initial_data.json",
            "group_test_data.json",
            "default_oauth_apps.json",
        ]

        call_command("loaddata", *fixture, **{"verbosity": 0, "database": "default"})
