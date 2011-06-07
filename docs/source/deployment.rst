Deploying your GeoNode Site
***************************

This page provides a high-level description of the software required to set up
a publicly accessible GeoNode web site.  Since deployment details will vary
between platforms this information is deliberately vague.  Some
platform-specific instructions are also available.  The platform-specific
guides are contributed by the community, so if you deploy on a new platform
please consider writing or updating a guide.

.. toctree::

   /deploy/centos
   /deploy/ubuntu
   /deploy/production


Recommended Minimum System Requirements
=======================================

For deployment of GeoNode on a single server, the following are the bare minimum system requirements:

* 2GB of RAM
* 2.2GHz processor.  (Additional processing power may be required for multiple concurrent styling renderings)
* 1 GB software disk usage.
* Additional disk space for any data hosted with GeoNode and tiles cached with GeoWebCache.
* 64-bit hardware recommended.

Java Web Applications (WARs)
============================

GeoNode requires a Java servlet container compatible with the J2EE standard,
2.5 or higher.  `Jetty <http://jetty.mortbay.org/>`_ and `Tomcat
<http://tomcat.apache.org/>`_ are two good free servlet containers.  See their
web sites for installation and application deployment instructions.

GeoNetwork with GeoNode Schema
------------------------------

GeoNode's GeoNetwork integration requires use of a customized metadata schema.
The GeoNode project provides a custom build of GeoNetwork with this extra
schema pre-installed.  This GeoNetwork is ready to run out-of-the-box; simply
deploy using your servlet container's usual mechanism.

Steps
+++++

1. *Deploy* GeoNetwork to your servlet container using the normal mechanism.
   For Tomcat and Jetty, this simply means placing ``geonetwork.war`` in the
   webapps subdirectory of the servlet container's installation directory.

2. *Configure* GeoNetwork by changing the administrative account password
   through GeoNetwork's web interface.  The administrative account username and
   password are both ``admin`` by default.

3. *Remove* the sample metadata records that are included with GeoNetwork by
   default.  To do so, you can simply perform a search with no terms, then use
   the 'Select all' link on the search results page to select all records in
   the GeoNetwork site.  Finally, use the 'actions on selection' menu to delete
   the records.

.. note:: 

    GeoNode releases do not include the Intermap service that normally
    accompanies GeoNetwork installations.  As a result, some JavaScript errors
    come up while performing searches.  These are not a problem.

GeoServer with GeoNode Extensions
---------------------------------

GeoNode's GeoServer integration requires some specific extensions to help
GeoNode in managing GeoServer layers.  GeoNode releases include a GeoServer WAR
archive with these extensions pre-installed.  However, some manual
configuration may still be needed.

Steps
+++++

1. *Deploy* GeoServer to your servlet container using the normal mechanism.
   For Tomcat and Jetty, this simply means placing
   ``geoserver-geonode-dev.war`` in the webapps subdirectory of the servlet
   container's installation directory.

2. *Configure* GeoServer with the location of the GeoNode site, used for
   authentication (so that GeoServer can recognize logins from the main site).
   This setting defaults to http://localhost:8000/, so if you are running
   the GeoNode Django application on a different port, or on a different server
   from the one running GeoServer, then you will need to change this by adding
   a block of XML to ``WEB-INF/web.xml`` within the unpacked application
   directory, like so::

       <context-param>
           <param-name>GEONODE_BASE_URL</param-name>
           <param-value>http://localhost:8080/</param-value>
       </context-param> 

   The ``<param-value>`` tag should enclose the URL to the Django application
   homepage.

Static Resources
----------------

The GeoNode project provides an archive of the minified JavaScript and CSS
resources used in the GeoNode site.  These media can simply be served with a
static file server such as Apache httpd or lighttpd.  See
http://httpd.apache.org/docs/2.2/urlmapping.html and
http://redmine.lighttpd.net/projects/lighttpd/wiki/Server.document-rootDetails
for information on configuring Apache httpd and lighttpd to serve files,
respectively.  Many other web servers are perfectly capable of serving these
files; Apache httpd and lighttpd are just examples.

Steps:
++++++

1. *Configure* a document root in your webserver, pointing to some directory on
   your filesystem.

2. *Extract* all the JavaScript and CSS files from the GeoNode release archive
   (geonode-client.zip) into the document root.

Django Web Application
----------------------

The GeoNode Django application should run in mod_wsgi under Apache httpd.
See the Django project's deployment documentation for more information.
However, we highly recommend using virtualenv to sandbox the GeoNode
dependencies from the rest of the Python software on your system.

Steps:
++++++

1. *Install virtualenv* if you do not already have it available.  It can easily
   be installed via easy_install or pip::
   
       $ easy_install virtualenv
       $ pip install virualenv
       
2. *Prepare a sandbox* for GeoNode using virtualenv::

       $ virtualenv geonode
       $ cd geonode
       $ source bin/activate

3. *Install* the geonode python modules from the Pip bundle::

       $ pip install geonode-webapp.pybundle

   If this step fails, make sure that you have a working C++ compiler installed
   and development versions of the requisite libraries, listed in the GeoNode
   README file.

4. *Configure* the geonode Django app by editing
   ``./src/GeoNodePy/geonode/settings.py``.  The available settings and their
   usage is described elsewhere in this documentation.

5. If running via fastcgi, you can use the django-admin.py script to launch the
   fastcgi server for Django.  If running via WSGI, ensure that the virtualenv
   is added to the python path for the WSGI script.  See the official `Django
   deployment documentation
   <http://docs.djangoproject.com/en/1.2/howto/deployment/>`_ for details.


Configuring User Registration
-----------------------------

You can optionally configure GeoNode to allow new users to register through the web.  New registrants will be sent an email inviting them to activate their account.

To allow new user registration:

1. Set up the email backend for Django (see `Django documentation <http://docs.djangoproject.com/en/dev/topics/email/#e-mail-backends>`_) and add the appropriate settings to ``./src/GeoNodePy/geonode/settings.py``.  For example::

       EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
       EMAIL_HOST = 'smtp.gmail.com'
       EMAIL_HOST_USER = 'foo@gmail.com'
       EMAIL_HOST_PASSWORD = 'bar'
       EMAIL_PORT = 587
       EMAIL_USE_TLS = True

2. One week activation window::

	   ACCOUNT_ACTIVATION_DAYS = 7 
	   
3. In the same settings file set::

       REGISTRATION_OPEN=True	   

4. With the Django application running, set the domain name of the service properly through the admin interface.  (This domain name is used in the account activation emails.)::

       http://localhost:8000/admin/sites/site/1

To register as a new user, click the ''Register'' link in the GeoNode index header.

Additional Configuration
------------------------

Some other things that require tweaking:

* Web-accessible uploads directory for user profile photos

* Configuring GeoNetwork/Django to use a "real" Postgres database instead of
  embedded ones.

* In order to generate the sitemap properly, the sites domain name must be set
  within the sites framework. This requires that an admin user login to the
  admin interface and navigate to the sites module and change example.com to the
  actual domain name (and port if applicable). The admin interface can be accessed
  at http://<host>:<port>/admin/sites/site/

* It is possible to 'inform' google of changes to your sitemap. This is accomplished
  using the ping_google management command. More information can be found here
  http://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/#django.contrib.sitemaps.ping_google
  It is recommended to put this call into a cron (scheduled) job to update google periodically.
