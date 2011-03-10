Deploying on CentOS 5
=====================

This page provides a guide to installing GeoNode on the CentOS Linux
distribution.  

.. note:: 

    While we intend to provide a detailed, accurate explanation of the
    installation process, it may become out of date.  If you run into problems
    with the process described in this document, please don't hesitate to let
    the GeoNode team know so we can keep it up to date.

The stack used is:

* *Servlet Container*: Apache Tomcat

* *Static File Server*: Apache httpd

* *Python/WSGI Container*: mod_wsgi

* *Django Database*: MySQL

Download GeoNode Release Archive
--------------------------------

You can get the latest release from http://geonode.org/ or the `GeoNode project
wiki <http://projects.opengeo.org/CAPRA/>`_ .  You can unpack it like::

  $ tar xvzf GeoNode-1.0-beta.tar.gz
  GeoNode-1.0-beta/geonetwork.war
  GeoNode-1.0-beta/pavement.py
  GeoNode-1.0-beta/geonode-client.zip
  GeoNode-1.0-beta/geonode-webapp.pybundle
  GeoNode-1.0-beta/geoserver-geonode-dev.war
  GeoNode-1.0-beta/bootstrap.py
  GeoNode-1.0-beta/deploy-libs.txt
  GeoNode-1.0-beta/deploy.ini.ex

Runtimes
--------

The Python interpreter in the CentOS repositories does not support GeoNode;
instead use the python26 package from the `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ project.  Follow the instructions from
the wiki to activate the EPEL repository, then install Python with::

    $ su -c 'yum install python26'

You will also need a Java Runtime Environment (JRE).  We recommend following
the `Oracle installation instructions
<http://www.oracle.com/technetwork/java/javase/install-linux-self-extracting-142296.html>`_
While other JRE versions will work, Oracle's is recommended for performance
reasons.  For the purposes of this guide we will assume that the JRE is
installed to :file:`/opt/sun-java-1.6.0_22/`

Servlet Container Installation
------------------------------

1. Fetch the Tomcat archive from http://tomcat.apache.org/downloads/ ::

     $ wget http://ftp.wayne.edu/apache//tomcat/tomcat-6/v6.0.29/bin/apache-tomcat-6.0.29.zip
 
2. Unpack the archive to :file:`/opt/apache-tomcat-{version}`; for example
   :file:`/opt/apache-tomcat-6.0.26/` ::

     $ unzip apache-tomcat-6.0.29.zip -d /opt/apache-tomcat-6.0.29/

3. Ensure the startup scripts are executable::

     $ chmod +x /opt/apache-tomcat-6.0.29/bin/*.sh

4. Edit :file:`/opt/apache-tomcat-6.0.29/bin/catalina.sh` to set the
   ``JAVA_HOME`` environment variable which is required to help Tomcat find
   some Java utilities.  This file starts with a long prologue comment
   documenting the environment variables which control various aspects of
   Tomcat's operation. Find the ``JAVA_HOME`` comment::

     #   JAVA_HOME       Must point at your Java Development Kit installation.
     #                   Required to run the with the "debug" argument.

   And insert a line following it specifying the appropriate value::

     JAVA_HOME=/opt/sun-java-1.6.0_22/

   In this same file, also set ``JAVA_OPTS`` to increase the available RAM and
   work around a JVM bug which affects GeoNetwork::

     JAVA_OPTS="-Xmx1024m -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement"

   .. note::

      Ensure that you *don't* include a leading ``#`` character in these lines;
      that makes them comments which have no effect.

5. You can now start Tomcat with the included startup script::

     $ /opt/apache-tomcat-6.0.29/bin/catalina.sh start

Deploying GeoNetwork
--------------------

1. Move :file:`geonetwork.war` from the GeoNode release archive into the Tomcat
   deployment directory::

     $ mv /tmp/GeoNode-1.0-beta/geonetwork.war /opt/apache-tomcat-6.0.29/webapps/

2. Tomcat will automatically extract the archive and start up the GeoNetwork
   service.  However, the administrative account will be using the default
   password.  You should navigate to `the GeoNetwork web interface
   <http://localhost:8080/geonetwork/>` and change the password for this
   account, taking note of the new password for later use.

Deploying GeoServer
-------------------

1. Move :file:`geoserver-geonode-dev.war` from the GeoNode release archive into
   the Tomcat deployment directory::

     $ mv /tmp/GeoNode-1.0-beta/geoserver-geonode-dev.war /opt/apache-tomcat-6.0.29/webapps/

2. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/opt/apache-tomcat-6.0.29/webapps/geoserver-geonode-dev/WEB-INF/web.xml` 
   and add a context-parameter::

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>

3. After modifying ``web.xml`` you will need to restart Tomcat for changes to
   take effect::

     $ /opt/apache-tomcat-6.0.29/bin/catalina.sh stop &&
       sleep 30 &&
       /opt/apache-tomcat-6.0.29/bin/catalina.sh start

4. You should now be able to visit the GeoServer web interface at
   http://localhost:8080/geoserver-geonode-dev/ .

Configuring Apache httpd
------------------------

1. Install the httpd package::

     $ su -c 'yum install httpd'

2. Create a new directory :file:`/opt/geonode/apache/` to contain the GeoNode
   web application files, including a subdirectory for 'media' such as CSS
   stylesheets and JavaScript scripts::

     $ mkdir -p /opt/geonode/apache/media/

3. Extract the :file:`geonode-client.zip` archive from the geonode release
   archive into the media directory that was just created::

     $ unzip /tmp/GeoNode-1.0-beta/geonode-client.zip -d /opt/geonode/apache/media/

4. Create a new configuration file in :file:`/etc/httpd/conf.d/geonode.conf` ::

     DocumentRoot "/opt/geonode/apache"
     Alias /media "/opt/geonode/apache/media"
     Alias /static "/opt/geonode/apache/static"
     <Directory "/opt/geonode/apache">
         AllowOverride None
         Order allow,deny
         Allow from all
     </Directory>

5. Start up the web server::

     $ service httpd start

6. You should now be able to browse through the static media files using your
   web browser.  You should be able to load the GeoNode header graphic from
   http://localhost/media/geonode-client/gn/theme/app/img/header-bg.png .

Installing the GeoNode Django Application
-----------------------------------------

1. Enable the `ELGIS testing repository
   <http://wiki.osgeo.org/wiki/Enterprise_Linux_GIS>`_

2. Install ``virtualenv``::

     $ su -c 'yum install python26-virtualenv'

3. Create a new virtualenv sandbox for the geonode application::
     
     $ virtualenv /opt/geonode/sandbox

4. Install the python modules from the :file:`geonode-webapp.pybundle` file in
   the sandbox directory::

     $ cd /opt/geonode/sandbox/
     $ source bin/activate
     $ easy_install pip
     $ pip install /tmp/GeoNode-1.0-beta/geonode-webapp.pybundle

5. Create a file with random text (this is used for internal HTTP transactions
   between the Django application and GeoServer)::

     $ python -c "import random; print ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890._/*$', 32))" | sudo tee /opt/geonode/sandbox/geoserver_token

6. Finally, create a Python file at
   :file:`/opt/geonode/sandbox/src/GeoNodePy/geonode/local_settings.py` to
   contain settings for the local deployment::

     DEBUG = False
     SERVE_MEDIA = False
     MINIFIED_RESOURCES = True

     DATABASE_NAME = '/opt/geonode/production.db'

     GEONODE_CLIENT_LOCATION = "http://demo.geonode.org/media/"

     GEOSERVER_BASE_URL = "http://localhost:8080/geoserver-geonode-dev/"
     GEONETWORK_BASE_URL = "http://localhost:8080/geonetwork/"

     MEDIA_URL = 'http://demo.geonode.org/static/'
     GEONODE_UPLOAD_PATH = '/opt/geonode/apache/static/'

     SITEURL = "http://localhost/"
     MEDIA_ROOT = '/opt/geonode/apache/media/'

Installing mod_wsgi
-------------------

1. Install mod_wsgi and Apache httpd::
     
     $ su -c 'yum install python26_mod_wsgi'

   .. note::
       The default CentOS package repository includes a ``mod_wsgi`` package
       which is distinct from the ``python26_mod_wsgi`` package provided by
       ELGIS.  Since GeoNode requires Python 2.6, it will not function with the
       default package, so please ensure that you install the package as listed
       above.

2. Create a short Python script in :file:`/opt/geonode/geonode.wsgi` to load
   the GeoNode application in Apache::

     #! /opt/geonode/sandbox/bin/python
     import os
     import site
     site.addsitedir('/opt/geonode/sandbox/lib/python2.6/site-packages')
     os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
     import django.core.handlers.wsgi
     application = django.core.handlers.wsgi.WSGIHandler()

3. Modify :file:`/etc/httpd/conf.d/wsgi.conf`; find the line that reads::

     #LoadModule wsgi

   and remove the ``#`` at the beginning so it reads::

     LoadModule wsgi

4. Edit the configuration file :file:`/etc/httpd/conf.d/geonode.conf` that was
   created earlier and add on to the end::

     WSGIDaemonProcess geonode python-path=/opt/geonode/sandbox/lib/python2.6/site-packages
     WSGIScriptAlias / /opt/geonode/geonode.wsgi
     WSGISocketPrefix /var/run/wsgi
     WSGIPassAuthorization On

5. Now restart the webserver::

     $ service httpd restart

   .. note:: 

     The GeoNode site won't be working just yet; you still need to
     initialize the database before it will work.

Prepare the Django database
---------------------------

1. Activate the GeoNode virtualenv if it is not already active::

     $ source bin/activate

2. Use the `django-admin` tool to initialize the database::

     $ django-admin.py syncdb --settings=geonode.settings

   This command should request a user name and password from you; these will be
   used for an admin account on the GeoNode site.

3. Use `django-admin` again to synchronize GeoServer, GeoNode, and GeoNetwork::
    
     $ django-admin.py updatelayers --settings=geonode.settings

   All three services must be running for this to work, but you can repeate the
   command as often as you like without creating duplicate records or
   overwriting pre-existing ones.  This can be used to add layers to a GeoNode
   site when the GeoNode upload tool can not handle those layers (for example,
   PostGIS layers fall under this category at presen  This can be used to add
   layers to a GeoNode site when the GeoNode upload tool can not handle those
   layers (for example, PostGIS layers fall under this category at present.) by
   simply re-running the updatelayers script after configuring the layers in
   GeoServer.

6. You should now be able to see the GeoNode site at http://localhost/


Miscellaneous Configuration
---------------------------

In order to generate the sitemap properly, the sites domain name must be set  
within the sites framework. This requires that an admin user login to the  
admin interface and navigate to the sites module and change example.com to the
actual domain name (and port if applicable). The admin interface can be accessed
at http://<host>:<port>/admin/sites/site/

It is possible to 'inform' google of changes to your sitemap. This is accomplished
using the ping_google management command. More information can be found here
http://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/#django.contrib.sitemaps.ping_google
It is recommended to put this call into a cron (scheduled) job to update google periodically.
