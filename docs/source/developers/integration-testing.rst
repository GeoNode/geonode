Integration Testing in GeoNode
==============================

GeoNode's integration testing suite requires a full deployment with live data for doing some rigorous testing.
This means that running the integration tests requires deploying GeoServer, GeoNetwork and the Django application, although it is possible to run the tests against those servers running in "development" mode.
To ensure repeatability of the tests, GeoNode should be **fully reset** between runs of the suite.

The integration test suite itself is maintained in a separate source repository from the main GeoNode code; it is available at http://github.com/GeoNode/geonode-integration.git/ .

Running against Paster and Tomcat Standalone
============================================

.. note::

    This configuration is good for Python developers who can afford to trade away ease of WAR redeployment for faster startup time.

Setup
.....

1: Fetch a standalone archive of Tomcat from http://tomcat.apache.org/ and unpack it::

   $ wget http://www.trieuvan.com/apache/tomcat/tomcat-6/v6.0.32/bin/apache-tomcat-6.0.32.zip
   $ unzip apache-tomcat-6.0.32.zip

2. Deploy GeoServer and GeoNetwork into the Tomcat ``webapps`` directory by copying the unpacked ZIP archives into the Tomcat ``webapps`` directory::

     $ unzip geonode/webapps/geonetwork.war -d webapps/geonetwork/
     $ unzip geonode/src/geoserver-geonode-ext/target/geoserver-geonode-ext.zip -d webapps/geoserver/

3. Create a Django fixture defining an administrative user named ``admin`` with the password ``admin``::

     (geonode) $ django-admin.py flush --settings=geonode.settings
     ## you will be prompted for the administrative credentials
     (geonode) $ django-admin.py dumpdata auth --settings=geonode.settings > admin.fixture.json

   .. note::

       Renaming the GeoNode webapp from ``geoserver-geonode-ext`` to ``geoserver`` matches more closely with the default configuration; if you choose a different name you should modify your ``local_settings.py`` to reflect that.

3. As GeoNetwork and GeoServer are modified you will need to periodically redeploy to Tomcat.
   You can do so by re-running the ``paver build`` command and then repeating step 2 above.

Resetting Before Test Runs
..........................

GeoNetwork, GeoServer, and the Django application should all be reset between runs of the integration testing suite.

**Reset Django** by issuing the following command::

    (geonode) $ django-admin.py flush --settings=geonode.settings --noinput \
        && django-admin.py loaddata admin.fixture.json --settings=geonode.settings

**Reset GeoServer** by deleting the data/ directory and replacing it with a clean copy::

    $ rm -rf apache-tomcat-6.0.32/webapps/geoserver/data/ && \
        cp -R geonode/gs-data/ apache-tomcat-6.0.32/webapps/geoserver/data/

**Reset GeoNetwork** by erasing the builtin database's storage directory::

    $ rm -rf apache-tomcat-6.0.32/webapps/geonetwork/WEB-INF/db/data/

After resetting, start Tomcat with::

    $ apache-tomcat-6.0.32/bin/catalina.sh run

and paster with::

    (geonode) $ paster serve --reload shared/dev-paste.ini

For subsequent test runs, it is safe to leave paster running, but Tomcat should be **shutdown before each reset** and not started until the data has been fully refreshed.

Run Tests
.........

The integration suite assumes that the ``updatelayers`` command has already been run, so do that::

   (geonode) $ django-admin.py updatelayers --settings=geonode.settings

Then the test suite can be run using the included ``runtests.sh`` script::

   $ cd geonode-integration && GEONODE_HOME=../geonode bash runtests.sh

Running against Paster and Jetty
================================

.. note::

    This configuration is recommended for developers who are doing Java development and need to frequently deploy rebuilt versions of GeoServer and/or GeoNetwork.

Setup
.....

1. Make a local backup of the sample ``gs-data`` which is downloaded during the ``paver build`` process::

   $ cp gs-data/ -R gs-data.bk/

2. Create a Django fixture defining an administrative user named ``admin`` with the password ``admin``::

   (geonode) $ django-admin.py flush --settings=geonode.settings
   (geonode) $ django-admin.py dumpdata auth --settings=geonode.settings > admin.fixture.json

Resetting Before Test Runs
..........................

GeoNetwork, GeoServer, and the Django application should all be reset between runs of the integration testing suite.

**Reset Django** by issuing the following command::
   
    (genode) $ django-admin.py flush --settings=geonode.settings --noinput \
        && django-admin.py loaddata admin.fixture.json --settings=geonode.settings

**Reset GeoServer** by deleting the data/ directory and replacing it with a clean copy::

    $ rm -rf gs-data/ && cp -R gs-data.bk/ gs-data/

**Reset GeoNetwork** by erasing the builtin database's storage directory::

    $ rm -rf webapps/geonetwork/WEB-INF/db/data/

After resetting, start Tomcat with::

    $ cd src/geoserver-geonode-ext/
    $ mvn jetty:run

and paster with::

    (geonode) $ paster serve --reload shared/dev-paste.ini

For subsequent test-runs, it is safe to leave paster running, but Tomcat should be **shutdown before each reset** and not started until the data has been fully refreshed.

Run Tests
.........

The integration suite assumes that the ``updatelayers`` command has already been run, so do that::

    (geonode) $ django-admin.py updatelayers --settings=geonode.settings

Then, the test suite can be run using the included ``runtests.sh`` script::

    $ cd geonode-integration && GEONODE_HOME=../geonode bash runtests.sh
