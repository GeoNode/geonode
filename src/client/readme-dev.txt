=================================
Running and deploying GeoExplorer
=================================

These instructions describe how to deploy GeoExplorer assuming you have a copy
of the application source code from subversion.

Getting a copy of the application
---------------------------------

To get a copy of the application source code, use subversion::

    you@prompt:~$ svn export http://svn.geoext.org/apps/opengeo/geoexplorer/branches/0.1.x/ geoexplorer


Running in development mode
---------------------------

Your copy of the application contains a debug.html file that loads the
application for debugging/development.  This file is not suitable for running
the application in production.  To view the application, open the debug.html
page in a browser (e.g. http://localhost/path/to/geoexplorer/debug.html).

Note that the inital configuration for the application works off of a remote
WMS and requires that you have a proxy set up locally.  See the debug.html
source for detail on configuration with a local WMS.


Connecting GeoExplorer to a local GeoServer
-------------------------------------------

The easiest way to run GeoExplorer is to place it in the www folder of a
GeoServer data dir.

1. Copy the geoexplorer root directory to $GEOSERVER_DATA_DIR/www/

2. Modify the "ows" configuration value in geoexplorer/debug.html to reflect the
path to your GeoServer WMS endpoint (usually "/geoserver/wms").

3. Open the debug.html page in a browser (e.g.
http://localhost:8080/geoserver/www/geoexplorer/debug.html)


Preparing the application for deployment
----------------------------------------

Running GeoExplorer as described above is not suitable for production because
JavaScript files will be loaded dynamically.  Before moving your application
to a production environment, follow the steps below.

1. Copy any changes to the app configuration you made in debug.html into the
geoexplorer/build/index.html file.  Just copy the changes to the JavaScript -
do not copy the entire contents of debug.html to index.html.

2. If you have not already set up JSTools, do so following the instructions
you find on the JSTools project page: http://pypi.python.org/pypi/JSTools

3. Use the Makefile in the build directory to create a standalone copy of the
application.

For example, to create a directory that can be moved to your production
environment, do the following::

    you@prompt:~$ cd geoexplorer/build
    you@prompt:~/geoexplorer/build$ make app

Move the GeoExplorer directory (from the build directory) to your production
environment.

If you want to create a zip archive of the application, instead run the
following:::

    you@prompt:~/geoexplorer/build$ make zip

