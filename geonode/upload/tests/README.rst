To run these tests, make sure a test db is setup:
  python manage.py syncdb --all

Create the admin user as per the above account credentials

Run geoserver. Make sure that geonode.upload is in INSTALLED_APPS:

  paver start_geoserver

While geoserver is running, run tests:

  REUSE_DB=1 python manage.py test geonode.upload.integrationtests

These tests will internally run a django server and modify the settings as
needed to adjust differences in configuration.

The upload tests will load a settings module to allow specification of a postgres
database other than what you might use for other local purposes. This module is:

  geonode.upload.tests.local_settings

If the `local_settings` or standard django settings do not enable a DB_DATASTORE,
the importer tests that import into the database will not run.

The `test_settings` module must also be supplied when launching the tests to run
the full suite including the DB_DATASTORE tests:

  DJANGO_SETTINGS_MODULE=geonode.upload.tests.test_settings python manage.py test geonode.upload.tests.integration

If there are existing layers in the test database, the tests will not run unless
the environment variable `DELETE_LAYERS` is present. For example:

  DELETE_LAYERS= python manage.py test geonode.upload.integrationtests

