=========
 GeoNode
=========

Build Requirements
==================

* Sun Java Development Kit 1.5 or Higher: http://java.sun.com/javase/downloads/index.jsp
  (Make sure to install the *JDK*!)
* Python 2.6: http://python.org/download/
* Apache Maven 2.0.10 or Later: http://maven.apache.org/download.html/

Install
=======

::

  svn co http://svn.opengeo.org/CAPRA/GeoNode/trunk/
  cd GeoNode
  python bootstrap.py
  . bin/activate
  paver build
  django-admin.py syncdb --settings=geonode.settings 
  paster serve shared/dev-paste.ini

Options
=======

For JavaScript Developers
-------------------------

JavaScript Developers can switch to using unminified scripts and CSS styles by 
setting the MINIFIED_RESOURCES entry in settings.py to False.  If you are developing JavaScript and testing against minified builds, make sure to use::

   $ paver concat_js 

to update the built script directory.

For Java Developers
-------------------

Java Developers can point the application at a particular GeoServer instance by setting the GEOSERVER_BASE_URL entry in settings.py to the context path of the GeoServer instance.  This should include the trailing slash.  For example, the default is::

    http://capra.opengeo.org/geoserver/

The GeoServer module in :file:`src/geonode-gs-ext/` is configured to stand up a GeoServer instance with the module ready on use of :command:`mvn jetty:run-war -DGEOSERVER_DATA_DIRECTORY=/path/to/data/` .  If you want to use this service, set::
  
    GEOSERVER_BASE_URL="http://localhost:8889/geoserver/"

