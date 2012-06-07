=========
 GeoNode
=========

Build Requirements
==================

Before starting work on the GeoNode, you will need to have the following
software installed and in your PATH:

* The git command-line client, version 1.5.3 or higher:
  - To verify that it is available, run ``git --version`` and verify the
    version is something like ``git version 1.6.6.1``
  - If not, you can download one of the installers from http://git-scm.com/ or
    from your operating system provider.

* Sun Java Development Kit 1.5 or Higher: 
  - To verify that it is available, run
    ``javac -help -version`` and verify that it reports a list of usage flags,
    ending with a line like ``javac 1.5.0_18`` (the numbers will vary with your
    installed version).
  - If not, download from http://java.sun.com/javase/downloads/index.jsp 
    (Make sure to install the *JDK*!) 

* Python 2.6:
  - To verify that it is available, run 
    ``python --version`` and verify that it reports a version number like
    ``Python 2.6``
  - If not, download from http://python.org/download/
  - Python must be compiled w/ SSL support and sqlite support to

    openssl development headers before building Python will suffice.

* Apache Maven 2.0.10 or Later:
  - To verify that it is available, run
    ``mvn -version`` and verify that it reports version information like::
        
      Maven version: 2.0.10
      Java version: 1.5.0_18
      OS name: "linux" version: "2.6.30.8-64.fc11.x86_64" arch: "amd64" Family: "unix"

  - If not, download from http://maven.apache.org/download.html

Additionally, GeoNode uses a number of native-code libraries in Python.  You
can install these libraries manually, or allow the GeoNode setup script to
compile them for you.   In the latter case, you will need to install a C
compiler such as GCC, as well as any requisite development libraries.  GCC
packages are available for Mac OSX and all Linux distributions; consult your
operating system provider for installation instructions.

The native libraries needed include:

* PIL http://www.pythonware.com/products/pil/

For GCC, packages are available for Mac OSX and all Linux distributions;
consult your operating system provider for installation instructions.  When
build PIL from source, ensure that you have development libraries available for
libpng, libjpeg, and libgif if you want to be able to use those formats in your
GeoNode site.

Install
=======

The following steps should prepare a Python virtual environment for you::

  git clone git://github.com/GeoNode/geonode.git geonode
  cd geonode
  virtualenv venv
  source venv/bin/activate
  pip install -r shared/dev-requirements.txt
  paver build
  django-admin.py createsuperuser --settings=geonode.settings
  paver start

Once fully started, you should see a message indicating the address of your geonode::
  
  Development GeoNode is running at http://localhost:8000/
  The GeoNode is an unstoppable machine
  Press CTRL-C to shut down


.. note:: 

  When running ``python bootstrap.py`` the ``--no-site-packages`` option is
  not required.  If enabled, the bootstrap script will sandbox your virtual
  environment from any packages that are installed in the system, useful if
  you have incompatible versions of libraries such as Django installed
  system-wide.  On the other hand, sometimes it is useful to use a version of
  the Python Imaging Library provided by your operating system
  vendor, or packaged other than on PyPI.  When in doubt, however, just leave
  this option in.


This command::

  django-admin.py createsuperuser --settings=geonode.settings

can be used to create additional administrative user accounts.  The administrative control panel is not
linked from the main site, but can be accessed at http://localhost:8000/admin/


.. Contact/Profile Notes::

    The GeoNode ``Contact`` model has been modified to use Idios
    in this branch. It has also been moved from the ``geonode.maps``
    module to ``geonode.people``.
    
    In terms of end user interface, there should be no difference.  
    However, the existing column ``maps_contact.user`` was modified
    to no longer accept null values.  The admin interface currently
    uses the class name ``Profiles`` for this model.
    
    Also, a ``User Type`` field has been added.  This field does not
    currently have an associated migration.

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
   ``http://localhost:8080/`` and run paver as described above.

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

* Now GeoNode is available in your browser at http://192.168.56.1:8000/


For Java Developers
-------------------

How GeoNode Finds GeoServer
...........................

Java Developers can point the application at a particular GeoServer instance by
setting the GEOSERVER_BASE_URL entry in settings.py to the context path of the
GeoServer instance.  This should include the trailing slash.  For example, the
GeoServer used for http://geonode.capra.opengeo.org/ is::

    http://geonode.capra.opengeo.org/geoserver/

The default value is ``http://localhost:8001/geoserver/``.  The GeoServer module
in :file:`src/geonode-geoserver-ext/` is configured to provide a GeoServer
instance at that port with the following commands::
   
    cd src/geonode-geoserver-ext/
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

Adding an email gateway to GeoNode can be very useful, the two main reasons are
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

In order to let people autoregister to the GeoNode, set::

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

GeoNode is Copyright 2010 OpenPlans.

GeoNode is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GeoNode is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with GeoNode.  If not, see <http://www.gnu.org/licenses/>.
