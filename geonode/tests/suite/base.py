from django.conf import settings
from django.core import management
from django.core.management import call_command
from django.db import connection

from django.db import transaction, DEFAULT_DB_ALIAS

real_commit = transaction.commit
real_rollback = transaction.rollback
# real_enter_transaction_management = transaction.enter_transaction_management
# real_leave_transaction_management = transaction.leave_transaction_management
real_savepoint_commit = transaction.savepoint_commit
real_savepoint_rollback = transaction.savepoint_rollback
# real_managed = transaction.managed

database = DEFAULT_DB_ALIAS

verbosity = 0
interactive = False

old_db_name = settings.DATABASES["default"]["NAME"]


def create_test_db(test_database_name):
    connection.settings_dict["TEST_NAME"] = test_database_name

    management.get_commands()
    management._commands["syncdb"] = "django.core"

    connection.creation.create_test_db(verbosity, autoclobber=not interactive)
    connection.settings_dict["NAME"] = test_database_name


def destroy_test_db(database_name):
    connection.creation.destroy_test_db(database_name, verbosity)


def load_db_fixtures(fixtures):
    call_command("loaddata", *fixtures)
