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

* *Django Database*: PostgreSQL

Download GeoNode Release Archive
--------------------------------
Release archives of geonode are produced from the geonode sources using::
 
  paver make_release # from the root of a working dir

If you don't have a checkout, you can get the latest release from
http://geonode.org (`(direct link) <http://dev.geonode.org/release/GeoNode-1.0.tar.gz>`_ . You can unpack it like::
 
  $ tar xvzf GeoNode-1.0.tar.gz
  GeoNode-1.0/geonetwork.war
  GeoNode-1.0/pavement.py
  GeoNode-1.0/geonode-client.zip
  GeoNode-1.0/geonode-webapp.pybundle
  GeoNode-1.0/geoserver-geonode-dev.war
  GeoNode-1.0/bootstrap.py
  GeoNode-1.0/deploy-libs.txt
  GeoNode-1.0/deploy.ini.ex

Runtimes
--------

Python:

The Python interpreter in the CentOS repositories does not support GeoNode;
instead use the python26 package from the `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ project.  Follow the instructions from
the wiki to activate the EPEL repository, then install Python with::

    $ su -c 'yum install python26'

Java:

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

     $ unzip apache-tomcat-6.0.29.zip -d /opt/

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
 
      The Java options used are as follows: 
      * ``-Xmx1024m`` tells Java to use 1GB of RAM instead of the default value
      * ``-XX:MaxPermSize=256M`` increase the amount of space used for
        "permgen", needed to run geonetwork/geoserver.
      * ``-XX:CompileCommand=...`` is a workaround for a JVM bug that affects
        GeoNetwork; see http://trac.osgeo.org/geonetwork/ticket/301

      Ensure that you *don't* include a leading ``#`` character in these lines;
      that makes them comments which have no effect.

5. You can now start Tomcat with the included startup script::

     $ /opt/apache-tomcat-6.0.29/bin/catalina.sh start

Deploying GeoNetwork
--------------------

1. Move :file:`geonetwork.war` from the GeoNode release archive into the Tomcat
   deployment directory::

     $ cp /tmp/GeoNode-1.0/geonetwork.war /opt/apache-tomcat-6.0.29/webapps/

Deploying GeoServer
-------------------

1. Move :file:`geoserver-geonode-dev.war` from the GeoNode release archive into
   the Tomcat deployment directory::

     $ cp /tmp/GeoNode-1.0/geoserver-geonode-dev.war /opt/apache-tomcat-6.0.29/webapps/

2. Tomcat will normally auto-deploy WARs upon startup, but in order to make
   some configuration changes, unpack it manually::
 
     $ cd /opt/apache-tomcat-6.0.29/webapps && unzip geoserver-geonode-dev.war -d geoserver-geonode-dev


3. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/opt/apache-tomcat-6.0.29/webapps/geoserver-geonode-dev/WEB-INF/web.xml` 
   and add a context-parameter::

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>



4. Move the GeoServer "data directory" outside of the servlet container to
   avoid having it overwritten on later upgrades::
 
      <context-param>
        <param-name>GEOSERVER_DATA_DIR</param-name>
        <param-value>/opt/geoserver_data/</param-value>
      </context-param>
 
   GeoServer requires a particular directory structure in data directories, so
   also copy the template datadir from the tomcat webapps directory::
 
      $ cp -R /opt/apache-tomcat-6.0.29/webapps/geoserver-geonode-dev/data/ /opt/geoserver_data
      $ chown tomcat6 -R /opt/geoserver_data/


 Changes after Tomcat is Running                                                                                         
-------------------------------

1. To restart tomcat::
  
     $ /opt/apache-tomcat-6.0.29/bin/catalina.sh stop & 
       sleep 30 &&
       /opt/apache-tomcat-6.0.29/bin/catalina.sh start

2. You should now be able to visit the GeoServer web interface at
   http://localhost:8080/geoserver-geonode-dev/ .  GeoServer is configured to
   use the Django database for authentication, so you won't be able to log in
    to the GeoServer console until Django is up and running.

3. The GeoNetwork administrative account will be using the default password.  You
   should navigate to `the GeoNetwork web interface
   <http://localhost:8080/geonetwork/>` and change the password for this account,
   taking note of the new password for later use. (Log in with the username
   ``admin`` and password ``admin``, then use the "Administration" link in the
   top navigation menu to change the password.)

4. (optional but recommended) GeoNetwork's default configuration includes
   several "sample" metadata records.  These can be listed by pressing the
   'search' button on the GeoNetwork homepage, without entering any search
   terms.  You can use the search results list to delete these metadata records
   so that they do not show up in GeoNode search results.

.. note::

    The GeoNetwork configuration, including metadata documents and password
    configuration, is stored inside of [tomcat]/webapps/geonetwork/ .  This
    directory can be copied between machines to quickly reproduce a
    configuration with a given administrative password across multiple
    machines.

Set up PostgreSQL
-----------------

1. Install the postgresql package::

     $ yum install postgresql

2. Create geonode database and geonode user account (you will be prompted for a password)::

     $ su - postgres
     $ createdb geonode && createuser -s -P geonode

.. seealso:: 

    See the Django setup notes for instructions on creating the database tables
    for the GeoNode app.


Install GeoNode Django Site
---------------------------

1. Install required libraries::

     $ yum install gcc libjpeg-dev libpng-dev python-gdal python-psycopg2

.. note::
       These may not be the names of those packages in Centos, please verify

2. Create new directories in /var/www/ for the geonode static files, uploads,
   and python scripts (``htdocs``, ``htdocs/media``, ``wsgi/geonode``,
   respectively)::
    
     $ mkdir -p /opt/geonode/{htdocs,htdocs/media,wsgi/geonode/}

3. Place the "static media" (aka JavaScript, CSS, and images) into the
   ``htdocs`` directory::

     $ unzip GeoNode-1.0/geonode-client/ -d /opt/geonode/htdocs/

4. Place the Python bundle and installer scripts into the ``wsgi/geonode``
   directory::
 
     $ cp bootstrap.py geonode-webapp.pybundle pavement.py /opt/geonode/

5. Use the bootstrap script to set up a virtualenv sandbox and install Python
   dependencies::

     $ cd /opt/geonode
     $ python bootstrap.py                 

6. Create a file
   ``/opt/geonode/src/GeoNodePy/geonode/local_settings.py``
   with appropriate values for the current server, for example::

     DEBUG = TEMPLATE_DEBUG = False
     MINIFIED_RESOURCES = True
     SERVE_MEDIA=False

     SITENAME = "GeoNode"
     SITEURL = "http://localhost/"

     DATABASE_ENGINE = 'postgresql_psycopg2'
     DATABASE_NAME = 'geonode'
     DATABASE_USER = 'geonode'
     DATABASE_PASSWORD = 'geonode-password'
     DATABASE_HOST = 'localhost'
     DATABASE_PORT = '5432'

     LANGUAGE_CODE = 'en'

     # the filesystem path where uploaded data should be saved
     MEDIA_ROOT = "/opt/geonode/htdocs/media/"

     # the web url to get to those saved files
     MEDIA_URL = SITEURL + "media/"

     GEONODE_UPLOAD_PATH = "/opt/geonode/htdocs/media/"

     # secret key used in hashing, should be a long, unique string for each
     # site.  See http://docs.djangoproject.com/en/1.2/ref/settings/#secret-key
     # 
     # Here is one quick way to randomly generate a string for this use:
     # python -c 'import random, string; print "".join(random.sample(string.printable.strip(), 50))'
     SECRET_KEY = '' 

     # The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
     GEOSERVER_BASE_URL = SITEURL + "geoserver-geonode-dev/"

     # The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
     GEONETWORK_BASE_URL = SITEURL + "geonetwork/"

     # The username and password for a user with write access to GeoNetwork
     GEONETWORK_CREDENTIALS = "admin", 'admin'

     # A Google Maps API key is needed for the 3D Google Earth view of maps
     # See http://code.google.com/apis/maps/signup.html
     GOOGLE_API_KEY = ""

     DEFAULT_LAYERS_OWNER='admin'

     GEONODE_CLIENT_LOCATION = SITEURL

7. Place a wsgi launcher script in /opt/geonode/wsgi/geonode.wsgi::

     import os
     os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
     from django.core.handlers.wsgi import WSGIHandler
     application = WSGIHandler()


8. Install the httpd package::

     $ su -c 'yum install httpd python26_mod_wsgi'

.. note::
       The default CentOS package repository includes a ``mod_wsgi`` package
       which is distinct from the ``python26_mod_wsgi`` package provided by
       ELGIS.  Since GeoNode requires Python 2.6, it will not function with the
       default package, so please ensure that you install the package as listed
       above.

9. Create a new configuration file in :file:`/etc/httpd/conf.d/geonode.conf` ::

     <VirtualHost *:80>
        ServerAdmin webmaster@localhost

        DocumentRoot /opt/geonode/htdocs/
        <Directory />
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        <Directory /opt/geonode/wsgi/>
            Options Indexes FollowSymLinks MultiViews
            AllowOverride None
            Order allow,deny
            allow from all
        </Directory>
        <Proxy *>
            Order allow,deny
            Allow from all
        </Proxy>

        ErrorLog /var/log/apache2/error.log

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        CustomLog /var/log/apache2/access.log combined

        Alias /geonode-client/ /opt/geonode/htdocs/geonode-client/
        Alias /media/ /opt/geonode/htdocs/media/
        Alias /admin-media/ /opt/geonode/lib/python2.6/site-packages/django/contrib/admin/media/

        WSGIPassAuthorization On
        WSGIScriptAlias / /opt/geonode/wsgi/geonode.wsgi
        WSGIDaemonProcess geonode python-path=/opt/geonode/lib/python2.6/site-packages
        WSGISocketPrefix /var/run/wsgi

        ProxyPreserveHost On

        ProxyPass /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPassReverse /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPass /geonetwork http://localhost:8080/geonetwork
        ProxyPassReverse /geonetwork http://localhost:8080/geonetwork
     </VirtualHost>

10. Set the filesystem ownership to the Apache user for the geonode/htdocs and wsgi folders::

      $ chown www-data -R /opt/geonode/{htdocs,wsgi}

11. Modify :file:`/etc/httpd/conf.d/wsgi.conf`; find the line that reads::

     #LoadModule wsgi

   and remove the ``#`` at the beginning so it reads::

     LoadModule wsgi

12. Now start the webserver::

     $ service httpd start

.. note:: 

     You should now be able to browse through the static media files using your
     web browser.  You should be able to load the GeoNode header graphic from
     http://localhost/geonode-client/gn/theme/app/img/header-bg.png .

     The GeoNode site won't be working just yet; you still need to
     initialize the database before it will work.

Prepare the Django database
---------------------------

1. Activate the GeoNode virtualenv if it is not already active::

     $ cd /opt/geonode
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
