Deploying your GeoNode Site
===========================

Java Web Applications (WARs)
----------------------------

GeoNode requires a Java servlet container compatible with the J2EE standard,
2.5 or higher.  `Jetty <http://jetty.mortbay.org/>`_ and `Tomcat
<http://tomcat.apache.org/>`_ are two good free servlet containers.  See their
web sites for installation and application deployment instructions.

GeoServer with GeoNode Extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GeoNode's GeoServer integration requires some specific extensions to help
GeoNode in managing GeoServer layers.  These extensions can be added to an
existing GeoServer installation by adding the JAR files to the GeoServer's
:file:`WEB-INF/lib/` and restarting GeoServer.  Alternatively, the GeoNode
project provides a custom build of GeoServer with these extensions installed.

GeoNetwork with GeoNode Schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GeoNode's GeoNetwork integration requires use of a customized metadata schema
that adds some social attributes to metadata documents.  The GeoNode project
provides a custom build of GeoServer with this extra schema pre-installed. 

Static Resources
----------------

The GeoNode project provides an archive of the minified JavaScript and CSS
resources used in the GeoNode site.  These media can simply be served with a
static file server such as Apache httpd or lighttpd.

Django Web Application
----------------------

The GeoNode Django application should be run in mod_wsg or mod_python under
Apache httpd.  See the Django project's deployment documentation for more
information.

Deployment Bundles
------------------
The GeoNode build script includes a `make_release` task which produces a file
archive containing the built WARs, GeoNode static media, and Django application
with dependencies.  Such an archive can be uploaded to a server and installed
without any further dependence on a network connection.
