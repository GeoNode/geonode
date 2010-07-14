Deploying GeoNode on Ubuntu
===========================

Software Used
-------------

* `Tomcat Servlet Container <http://tomcat.apache.org/>`_ for Java services

* `Apache httpd <http://httpd.apache.org/>`_ with 
  `mod_wsgi <http://modwsgi.googlecode.com/>`_ for Python web application

* `lighttpd <http://lighttpd.net/>`_ for static file hosting and proxying

Tomcat Configuration
--------------------

Although Ubuntu does provide a software package for Tomcat, the security policy
included with that package does not work well with GeoServer.  It is easier to
just use the ZIP package from the Tomcat downloads page::

    $ cd /opt/
    $ unzip ~/Downloads/apache-tomcat-6.0.26.zip
    $ sh /opt/apache-tomcat-6.0.26/bin/startup.sh

.. note::

   It would be nice to add an init.d script here too

.. note::

   We should provide instructions for setting up a geonode user to run all this
   stuff

Tomcat has the auto-deployer enabled by default, so we can deploy GeoServer and
GeoNetwork by simply placing the .WAR files in Tomcat's webapps directory::

    $ cp /opt/geonode-packages/{geoserver,geonetwork}.war \
    > /opt/apache-tomcat-6.0.26/webapps/

.. note:: 
   
   It really would be better to set GeoServer and GeoNetwork up with a
   Postgres/PostGIS database for performance/maintenance reasons.  How do you
   do that?

httpd (Apache) Configuration
----------------------------

For Apache, the Ubuntu package works fine.  Installing it is therefore pretty
straightforward::

    $ aptitude install apache2 mod_wsgi

Then write an httpd configuration file to hook up Django to mod_wsgi. You will
also need a .wsgi loader script.  Virtualenv is recommended.
