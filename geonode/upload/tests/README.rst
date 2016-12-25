To run the integration tests, make sure a the sqlite db is setup::

  python manage.py migrate

Run geoserver but ensure that the django server is _not_ running::

  paver start_geoserver

While geoserver is running, run tests::

  python manage.py test geonode.upload.tests.integration

Or, run a specific test class or single test (leave out the dot if no test)::

  python manage.py test geonode.upload.tests.integration:<class>.<test?>

These tests will internally run a django server and modify the settings as
needed to adjust differences in configuration. They will also create a user
named `test_uploader` and delete any layers this user owns prior to running.

The upload tests will load a settings module to allow specification of a postgres
database other than what you might use for other local purposes. This module is::

  geonode.upload.tests.test_settings

If the settings do not set the name of the OGC_SERVER DATASTORE option,
the importer tests that import into the database will not run.

The `test_settings` module must also be supplied when launching the tests to run
the full suite including the DATASTORE tests::

  DJANGO_SETTINGS_MODULE=geonode.upload.tests.test_settings python manage.py test geonode.upload.tests.integration
