=========
 GeoNode
=========

Directory Structure
===================

* docs/ - ?? I think this is to help paver find our docs so whit doesn't have
  to maintain two checkouts to build them.
* hazard.json - a data dump for the hazard categories
* package - this directory is where distributable bundles of the GeoNode pieces
  end up (in theory? I don't think we used this for the most recent deployment)
* pavement.py - the main build script for everything
* paver-minilib.zip - a zip archive of the paver library used by pavement.py
* setup.py - a shim to make the entire GeoNode source tree look like a Python
  package.  This probably should not be there since our Python modules have
  their own source tree with a setup.py now.
* shared/ - where "build configuration" lives.  This includes some dependency
  lists for the Python modules and stuff like the ini file with the location
  of the sample data archive.
* src/ - where the source code for the actual project lives.  This is divided
  up like so:
    * capra-client/ - the JavaScript/CSS for CAPRA-specific extensions
      (MyHazard) to the GeoNode core
    * geonode-client/ - the JavaScript/CSS for general apps (the Map editor,
      search, embedded viewer...)
    * GeoNodePy/ - the Python/Django modules.  Inside, geonode/ is the "core"
      and capra/ contains CAPRA-specific extensions.
    * geoserver-geonode-ext/ - the GeoServer extensions used by the GeoNode.
      Actually, the build script for this project is set up to create a WAR
      that includes those extensions, not just a bundle with the extension.

Build Requirements
==================
Before starting work on the GeoNode, you will need to have the following
software installed and in your PATH:

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
    support the geonode development setup.  Installing the sqlite and
    openssl development headers will suffice.

* Apache Maven 2.0.10 or Later:
  - To verify that it is available, run
    ``mvn -version`` and verify that it reports version information like::
        
      Maven version: 2.0.10
      Java version: 1.5.0_18
      OS name: "linux" version: "2.6.30.8-64.fc11.x86_64" arch: "amd64" Family: "unix"

  - If not, download from http://maven.apache.org/download.html/

Install
=======

::

  svn co http://svn.opengeo.org/CAPRA/GeoNode/trunk/ GeoNode
  cd GeoNode
  python bootstrap.py
  . bin/activate
  paver build
  paver host 

Options
=======

For JavaScript Developers
-------------------------

JavaScript Developers can switch to using unminified scripts and CSS styles by
setting the MINIFIED_RESOURCES entry in :file:`src/geonode/settings.py` to
``False``.  If you are developing JavaScript and testing against minified builds,
make sure to use::

   $ paver concat_js 
   $ paver capra_js

to update the built script directories for the base GeoNode site and the CAPRA
extensions, respectively.

For Java Developers
-------------------

Java Developers can point the application at a particular GeoServer instance by
setting the GEOSERVER_BASE_URL entry in settings.py to the context path of the
GeoServer instance.  This should include the trailing slash.  For example, the
GeoServer used for http://capra.opengeo.org/ is::

    http://capra.opengeo.org/geoserver/

The default value is ``http://localhost:8001/geoserver/``.  The GeoServer module
in :file:`src/geonode-geoserver-ext/` is configured to provide a GeoServer
instance at that port with the following commands::
   
    cd src/geonode-geoserver-ext/
    mvn jetty:run-war

If you want to change this service URL, edit :file:`src/geonode/settings.py` and
change the line::
  
    GEOSERVER_BASE_URL="http://localhost:8001/geoserver/"

to indicate the GeoServer URL that you want to use. 

This server defaults to using :file:`gs-data/` as the data directory by default.
If you need you need to use an alternative data directory, you can specify it
via the command line, using a command like::
 
    mvn jetty:run-war -DGEOSERVER_DATA_DIR=/home/me/mydata/ 
