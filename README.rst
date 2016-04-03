=========
 WorldMap
=========

Build Requirements 
==================

Before starting work on WorldMap, you will need to have the following
software installed and in your PATH:

* The git command-line client, version 1.5.3 or higher:
  - To verify that it is available, run ``git --version`` and verify the
    version is something like ``git version 1.6.6.1``
  - If not, you can download one of the installers from http://git-scm.com/ or
    from your operating system provider.

* The Subversion command-line client, version 1.5 or higher.
  - To verify that is is available, run ``svn --version`` and verify the output
    starts with something like ``svn, version 1.6.9 (r901367)``
  - If not, you can find the appropriate installer at
    http://subversion.apache.org/packages.html

* The GEOS geometry handling library: http://trac.osgeo.org/geos/

* The GDAL geographic raster access library: http://www.gdal.org/

* The OGR geographic vector data access library: http://www.gdal.org/ogr/

* Sun Java Development Kit 1.5 or Higher: 
  - To verify that it is available, run
    ``javac -help -version`` and verify that it reports a list of usage flags,
    ending with a line like ``javac 1.5.0_18`` (the numbers will vary with your
    installed version).
  - If not, download from http://java.sun.com/javase/downloads/index.jsp 
    (Make sure to install the *JDK*!) 

* Python 2.7:
  - To verify that it is available, run 
    ``python --version`` and verify that it reports a version number like
    ``Python 2.7``
  - If not, download from http://python.org/download/
  - Python must be compiled w/ SSL support and sqlite support to
    support the WorldMap development setup.  Installing the sqlite and
    openssl development headers before building Python will suffice.

* Apache Maven 2.0.10 or Later:
  - To verify that it is available, run
    ``mvn -version`` and verify that it reports version information like::
        
      Maven version: 2.0.10
      Java version: 1.5.0_18
      OS name: "linux" version: "2.6.30.8-64.fc11.x86_64" arch: "amd64" Family: "unix"

  - If not, download from http://maven.apache.org/download.html

* Apache Tomcat 6.x or Jetty

* Apache Ant

* PostgreSQL 8.x and PostGIS 1.5


Additionally, WorldMap uses a number of native-code libraries in Python.  You
can install these libraries manually, or allow the WorldMap setup script to
compile them for you.   In the latter case, you will need to install a C
compiler such as GCC, as well as any requisite development libraries.  GCC
packages are available for Mac OSX and all Linux distributions; consult your
operating system provider for installation instructions.

The native libraries needed include:

* PIL http://www.pythonware.com/products/pil/

* libxml2-dev

* libxslt-dev

For GCC, packages are available for Mac OSX and all Linux distributions;
consult your operating system provider for installation instructions.  When
build PIL from source, ensure that you have development libraries available for
libpng, libjpeg, and libgif if you want to be able to use those formats in your
WorldMap site.


Install
=======


The following steps should prepare a Python virtual environment for you.  Note that you will need 
to manually create a PostGIS datbase and user first.  The default connection settings are
stored in src/GeoNodePy/geonode/settings.py:
database name: wm_db
user: wm_user
password: wm_password

Postgres database creation
--------------------------

  PostGIS 1.5
  ===========

  # create user
  create role wm_user password 'wm_password' superuser login;
  # create wm_db
  psql -U postgres -c "create database wm_db with owner wm_user encoding 'UTF8' lc_collate='en_US.utf8' lc_ctype='en_US.utf8' template template0;"
  psql -U wm_user -d wm_db -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
  psql -U wm_user -d wm_db -f /usr/share/postgresql/9.1/contrib/postgis_comments.sql
  psql -U wm_user -d wm_db -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql

  # create wmdata
  psql -U postgres -c "create database wmdata with owner wm_user encoding 'UTF8' lc_collate='en_US.utf8' lc_ctype='en_US.utf8' template template0;"
  psql -U wm_user -d wmdata -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
  psql -U wm_user -d wmdata -f /usr/share/postgresql/9.1/contrib/postgis_comments.sql
  psql -U wm_user -d wmdata -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql


  PostGIS 2.0+
  ===========

  # create user
  createuser -P -s -E -l wm_user;

  #create PostGIS template with legacy GIST operators
  createdb -E UTF8 -O wm_user template_postgis
  psql -U postgres -d template_postgis -c "CREATE EXTENSION postgis;"
  psql -U postgres -d template_postgis -f geonode/static/geonode/patches/postgis/legacy_gist.sql

  # create wm_db
  createdb -E UTF8 -U wm_user -T template_postgis wm_db

  # create wmdata
  createdb -E UTF8 -U wm_user -T template_postgis wmdata

GeoNode installation
--------------------

  git clone git://github.com/cga-harvard/cga-worldmap.git cga-worldmap
  
  cd cga-worldmap
  
  git submodule update --init
  
  mkvirtualenv worldmap

  pip install -r shared/requirements.txt
  
  paver build # see note2 below
  
  django-admin.py createsuperuser --settings=geonode.settings


Start the server:
  paver host


Once fully started, you should see a message indicating the address of your WorldMap::
  
  Development GeoNode is running at http://localhost:8000/
  The GeoNode is an unstoppable machine
  Press CTRL-C to shut down


* note1::

  When running ``python bootstrap.py`` the ``--no-site-packages`` option is
  not required.  If enabled, the bootstrap script will sandbox your virtual
  environment from any packages that are installed in the system, useful if
  you have incompatible versions of libraries such as Django installed
  system-wide.  On the other hand, sometimes it is useful to use a version of
  the Python Imaging Library provided by your operating system
  vendor, or packaged other than on PyPI.  When in doubt, however, just leave
  this option in.

* note2::

  When running "pave build" command, if error about version string parsing occurs, 
  edit ~/cga-worldmap/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py,
  search for "ver = geos_version()" under "def geos_version_info()", 
  edit "ver = geos_version()" to "ver = geos_version().split(' ')[0]".
  In this case the space between the version will be deleted.
  Finally, run "pave build" again.

This command::

  django-admin.py createsuperuser --settings=geonode.settings

can be used to create additional administrative user accounts.  The administrative control panel is not
linked from the main site, but can be accessed at http://localhost:8000/admin/

Options
=======

For JavaScript Developers
-------------------------

Minified Scripts
................

JavaScript Developers can switch to using unminified scripts and CSS:

1. Get and run geonode-client:

    $ git clone git://github.com/GeoNode/geonode-client.git geonode-client
    $ cd geonode-client
    $ ant init debug

2. Set the GEONODE_CLIENT_LOCATION entry in :file:`src/geonode/settings.py` to
   ``http://localhost:9090/`` and run paver as described above.

Note that this requires ant (http://ant.apache.org/) in addition to the above
build requirements.

VirtualBox Setup
................

To test the application in different browsers in VirtualBox guests, the
following needs to be done before running ``paver host``:

* Start the guest in VirtualBox. Set the network adapter mode to
  "Host-only adapter". Then set it back to "NAT".

* On the host, do ifconfig and write down the IP address of the vboxnet0
  adapter.

* Edit :file:`src/GeoNodePy/geonode/settings.py` and change the line::

    GEOSERVER_BASE_URL="http://localhost:8001/geoserver/"

  to use the IP address you have written down above::

    GEOSERVER_BASE_URL="http://192.168.56.1:8001/geoserver/"

* Make sure to change other http://localhost urls in
  :file:`src/GeoNodePy/geonode/settings.py` accordingly as well

* To start the web server, run::

    $ paver host -b 192.168.56.1

* Now WorldMap is available in your browser at http://192.168.56.1:8000/


For Java Developers
-------------------

How WorldMap Finds GeoServer
...........................

Java Developers can point the application at a particular GeoServer instance by
setting the GEOSERVER_BASE_URL entry in settings.py to the context path of the
GeoServer instance.  This should include the trailing slash.  For example, the
GeoServer used for http://geonode.capra.opengeo.org/ is::

    http://geonode.capra.opengeo.org/geoserver/

The default value is ``http://localhost:8001/geoserver/``.  The GeoServer module
in :file:`src/geoserver-geonode-ext/` is configured to provide a GeoServer
instance at that port with the following commands::
   
    cd src/geoserver-geonode-ext/
    sh startup.sh

.. note:: 
    Normally, ``mvn jetty:run-war`` would be sufficient.  However, we use the
    shell script to add some extra parameters to the JVM command-line used to
    run Jetty in order to workaround a JVM bug that affects GeoNetwork.

If you want to change this service URL, edit :file:`src/geonode/settings.py` and
change the line::
  
    GEOSERVER_BASE_URL="http://localhost:8001/geoserver/"

to indicate the GeoServer URL that you want to use. 

To run the Django app when Jetty is started independently, use::

    paster serve --reload shared/dev-paste.ini

in the base of your working directory.


Alternative GeoServer Data Directories
......................................

This server defaults to using :file:`gs-data/` as the data directory by default.
If you need you need to use an alternative data directory, you can specify it
by editing ``startup.sh`` to specify a different data directory::
 
    -DGEOSERVER_DATA_DIR=/home/me/mydata/ 

For Deployment
--------------

Email
.....

Adding an email gateway to WorldMap can be very useful, the two main reasons are
the ``ADMINS`` and ``REGISTRATION_OPEN`` settings explained below.

Here is a sample configuration to setup a Gmail account as the email gateway::

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = 'foo@gmail.com'
    EMAIL_HOST_PASSWORD = 'bar'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True

More informacion can be found in the django docs::

    http://docs.djangoproject.com/en/dev/ref/settings/?from=olddocs#email-backend

ADMINS
......

When ``DEBUG=False`` django will not display the usual error page, but will
email the people in the ADMINS tuple with the error traceback::

    ADMINS = (
        ('Carlos Valderrama', 'carlos.valderrama@gmail.com'),
        ('Diego Maradona', 'diego.maradona@gmail.com'),
    )

REGISTRATION_OPEN
.................

In order to let people autoregister to the WorldMap, set::

    REGISTRATION_OPEN=True

This needs email to be configured and your website's domain name properly set in
the Sites application (the default is example.com)::

    http://localhost:8000/admin/sites/site/1


POSTGIS INTEGRATION
.................
To automatically import uploaded shapefiles to a PostGIS database, open the settings.py file and set  'DB_DATASTORE' to 'True'.
Then assign the appropriate connection values to the other DB_DATASTORE_* settings below it:

DB_DATASTORE_NAME = '<Name of your PostGIS database>'
DB_DATASTORE_USER = '<Database user name>'
DB_DATASTORE_PASSWORD = '<Database user password>'
DB_DATASTORE_HOST = '<Database hostname (typically localhost)'
DB_DATASTORE_PORT = '<Database port (typically 5432)>'
DB_DATASTORE_TYPE='postgis'


TILE CACHING
.............
Create or edit the 'gwc-gs.xml' file under the gwc directory within your GeoServer data directory:
<GeoServerGWCConfig>
   <directWMSIntegrationEnabled>true</directWMSIntegrationEnabled>
   <WMSCEnabled>true</WMSCEnabled>
   <WMTSEnabled>true</WMTSEnabled>
   <TMSEnabled>true</TMSEnabled>
   <cacheLayersByDefault>true</cacheLayersByDefault>
   <cacheNonDefaultStyles>true</cacheNonDefaultStyles>
   <metaTilingX>4</metaTilingX>
   <metaTilingY>4</metaTilingY>
   <defaultCachingGridSetIds>
     <string>EPSG:900913</string>
   </defaultCachingGridSetIds>
   <defaultCoverageCacheFormats>
     <string>image/jpeg</string>
   </defaultCoverageCacheFormats>
   <defaultVectorCacheFormats>
     <string>image/png</string>
   </defaultVectorCacheFormats>
   <defaultOtherCacheFormats>
     <string>image/png</string>
   </defaultOtherCacheFormats>
</GeoServerGWCConfig>


GAZETTEER
..............
The gazetteer is disabled by default because it adds a bit of complexity to the setup process.
It should be enabled only if PostGIS integration is also enabled.

In your settings.py file:
* uncomment the following in INSTALLED_APPS:
    * #geonode.gazetteer,
* uncomment and modify if necessary the entire "GAZETTEER SETTINGS" section

If you want to enable full-text search for the gazetteer, run the following commands in the DB_DATASTORE database:
    ALTER TABLE gazetteer_gazetteerentry ADD COLUMN placename_tsv tsvector;
    CREATE INDEX placename_tsv_index on gazetteer_gazetteerentry using gin(placename_tsv);
    UPDATE gazetteer_gazetteerentry SET text_search =
         to_tsvector('english', coalesce(place_name,''));
    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
      ON gazetteer_gazetteerentry FOR EACH ROW EXECUTE PROCEDURE
      tsvector_update_trigger(placename_tsv, 'pg_catalog.english', place_name);

and then set GAZETTEER_FULLTEXTSEARCH = True in settings



QUEUE
..............
WorldMap can now optionally make use of Celery (http://celeryproject.org/) to send certain tasks (updating
the gazetteer, updating layer boundaries after creating/editing features) to a job queue
where they will be processed later.

In your settings.py file, uncomment the following in INSTALLED_APPS:
* #'geonode.queue',
* #'djcelery',
* #'djkombu',

The run interval is determined by QUEUE_INTERVAL - the default is 10 minutes.

You will need to manually setup and run the celery processes on your server.  For basic
instructions on doing so see  :file:`docs/deploy/celery_queue.txt`



ALTERNATE LAYER-SPECIFIC SECURITY SYSTEM
...........................................................................................
Place config.xml file in geoserver's data/security/auth/geonodeAuthProvider:

<org.geonode.security.GeoNodeAuthProviderConfig>
  <id>-53e27318:1396869cb2d:-7fef</id>
  <name>geonodeAuthProvider</name>
  <className>org.geonode.security.GeoNodeAuthenticationProvider</className>
  <baseUrl>http://localhost:8000/</baseUrl>
</org.geonode.security.GeoNodeAuthProviderConfig>

Change baseUrl if necessary.


In WEB-INF/web.xml, add the following, and change the user/password values:
    <context-param>
        <param-name>org.geonode.security.databaseSecurityClient.url</param-name>
        <param-value>jdbc:postgresql://localhost:5432/worldmap?user=wmuser&amp;password=wmus3r2012</param-value>
    </context-param>

Add the function in src/geoserver-geonode-ext/src/main/resources/org/geonode/security/geonode_authorize_layer.sql to the worldmap database



Directory Structure
===================

* docs/ - Documentation based on Sphinx
* pavement.py - Main build script.
* shared/ - Configuration files and support files for the installer.
* src/ - Source code for the java, javascript and python modules. Split in:

    * geonode-client/ - the JavaScript/CSS for general apps (the Map editor,
      search, embedded viewer...)
    * GeoNodePy/ - the Python/Django modules.  Inside, geonode/ is the "core".
    * geoserver-geonode-ext/ - the GeoServer extensions used by the GeoNode.
      Actually, the build script for this project is set up to create a WAR
      that includes those extensions, not just a bundle with the extension.

GPL License
=======

WorldMap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

WorldMap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with WorldMap.  If not, see <http://www.gnu.org/licenses/>.

WorldMap is Copyright 2014 President and Fellows of Harvard College

