Deploying on Ubuntu 10.04
=========================

This page provides a guide to installing GeoNode on the Ubuntu Linux
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

* *Django Database*: PostgresQL

Download GeoNode Release Archive
--------------------------------
Release archives of geonode are produced from the geonode sources using::

  paver make_release # from the root of a working dir

If you don't have a checkout, you can get the latest release from
http://geonode.org (`(direct link) <http://dev.geonode.org/release/GeoNode-1.0.tar.gz>`_ . You can unpack it like::

  $ cd /tmp
  $ wget http://dev.geonode.org/release/GeoNode-1.0.tar.gz
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

Python::

  $ sudo apt-get install python python-dev

Java:

For Sun/Oracle Java (recommended for better rendering performance)::

  $ sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
  $ sudo apt-get update
  $ sudo apt-get install sun-java6-jre

For OpenJDK (simpler install)::

  $ sudo apt-get install openjdk-6-jre

Servlet Container Installation
------------------------------

1. Install Tomcat using the package manager::

  $ sudo apt-get install tomcat6

2. Edit the JAVA_OPTS variable in the /etc/defaults/tomcat6 file (line 43) so it looks like this::

  JAVA_OPTS="${JAVA_OPTS} -XX:+UseConcMarkSweepGC -Xmx1024m -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement"

   .. note::

      The Java options used are as follows:
      * ``-Xmx1024m`` tells Java to use 1GB of RAM instead of the default value
      * ``-XX:MaxPermSize=256M`` increase the amount of space used for
        "permgen", needed to run geonetwork/geoserver.
      * ``-XX:CompileCommand=...`` is a workaround for a JVM bug that affects
        GeoNetwork; see http://trac.osgeo.org/geonetwork/ticket/301

Deploying GeoNetwork
--------------------

1. Move :file:`geonetwork.war` from the GeoNode release archive into the Tomcat
   deployment directory::

     $ sudo cp /tmp/GeoNode-1.0/geonetwork.war /var/lib/tomcat6/webapps/

Deploying GeoServer
-------------------

1. Move :file:`geoserver-geonode-dev.war` from the GeoNode release archive into
   the Tomcat deployment directory::


     $ sudo cp /tmp/GeoNode-1.0/geoserver-geonode-dev.war /var/lib/tomcat6/webapps/

2. Tomcat will normally auto-deploy WARs upon startup, but in order to make
   some configuration changes, unpack it manually::

     $ cd /opt/apache-tomcat-6.0.29/webapps && unzip geoserver-geonode-dev.war -d geoserver-geonode-dev

3. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/var/lib/tomcat6/webapps/geoserver-geonode-dev/WEB-INF/web.xml`
   and add a context-parameter::
 
     $ sudo vim /var/lib/tomcat6/webapps/geoserver-geonode-dev/WEB-INF/web.xml

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>

.. note::

   If you have more than one website running in apache using http://localhost will not work.
   In that case you need to set explicitly the name of the virtual host, for example:
   http://geonode.mycompany.net

4. Move the GeoServer "data directory" outside of the servlet container to
   avoid having it overwritten on later upgrades::

     <context-param>
       <param-name>GEOSERVER_DATA_DIR</param-name>
       <param-value>/opt/geonode_data/geodata</param-value>
     </context-param>

   GeoServer requires a particular directory structure in data directories, so
   also copy the template datadir from the tomcat webapps directory::

     $ sudo mkdir -p /opt/geonode_data/
     $ sudo cp -R /var/lib/tomcat6/webapps/geoserver-geonode-dev/data/ /opt/geonode_data/geodata
     $ sudo chown tomcat6 -R /opt/geonode_data/geodata

Changes after Tomcat is Running
-------------------------------

1. To restart tomcat::

     $ sudo /etc/init.d/tomcat6 restart

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

     $ sudo apt-get install postgresql

2. Create geonode database and geonode user account (you will be prompted for a password)::

     $ sudo su - postgres
     $ createdb geonode && createuser -s -P geonode
     $ exit

.. seealso:: 

    See the Django setup notes for instructions on creating the database tables
    for the GeoNode app.

Install GeoNode Django Site
---------------------------

1. Install required libraries::

     $ sudo apt-get install gcc libjpeg-dev libpng-dev python-gdal python-psycopg2 libgdal1-dev libproj-dev

2. Create new directories in ``/opt/geonode/`` for the geonode static files, uploads,
   and apache configuration (``static``, ``static/media``, ``wsgi``,
   respectively)::

     $ sudo mkdir -p /opt/geonode_data/{static,static/media,wsgi}

3. Place the "static media" (aka JavaScript, CSS, and images) into the
   ``static`` directory::

     $ sudo apt-get install unzip
     $ sudo unzip /tmp/GeoNode-1.0/geonode-client.zip -d /opt/geonode_data/static/

4. Place the Python bundle and installer scripts into the ``/opt/geonode``
   directory::

     $ sudo mkdir -p /opt/geonode
     $ cd /tmp/GeoNode-1.0/
     $ sudo cp bootstrap.py geonode-webapp.pybundle pavement.py /opt/geonode/

5. Use the bootstrap script to set up a virtualenv sandbox and install Python
   dependencies::

     $ cd /opt/geonode/
     $ sudo python bootstrap.py

.. note::

     You can avoid having to run bootstrap.py with sudo by changing the ownership of the
     /opt/geonode directory to the current user, or better than that, by creating a geonode user.

6. Create a file ``/opt/geonode_data/local_settings.py``
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
     MEDIA_ROOT = "/opt/geonode_data/static/media/"

     # the web url to get to those saved files
     MEDIA_URL = SITEURL + "media/"

     GEONODE_UPLOAD_PATH = MEDIA_ROOT

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

   After the ``local_settings.py`` file is created, symlink it to the location where it should be::

     sudo ln -s /opt/geonode_data/local_settings.py /opt/geonode/src/GeoNodePy/geonode/local_settings.py

.. note::

     The local_settings.py approach is a Django idiom to help customizing websites, it works because
     the last line of ``src/GeoNodePy/geonode/settings.py`` imports it if it exists. 

7. Place a wsgi launcher script in /opt/geonode_data/wsgi/geonode.wsgi::

     import os
     os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
     from django.core.handlers.wsgi import WSGIHandler
     application = WSGIHandler()

8. Install the httpd package::

     $ sudo apt-get install apache2 libapache2-mod-wsgi

9. Create a new configuration file in 
   :file:`/opt/geonode_data/geonode.apache` ::

     WSGIDaemonProcess geonode python-path=/opt/geonode/lib/python2.6/site-packages
     WSGIImportScript /opt/geonode_data/wsgi/geonode.wsgi process-group=geonode application-group=%{GLOBAL}
     <VirtualHost *:80>
        ServerAdmin webmaster@localhost

        DocumentRoot /opt/geonode_data/static/
        <Directory />
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        <Directory /opt/geonode_data/wsgi/>
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

        Alias /geonode-client/ /opt/geonode_data/static/geonode-client/
        Alias /media/ /opt/geonode_data/static/media/
        Alias /admin-media/ /opt/geonode/lib/python2.6/site-packages/django/contrib/admin/media/

        WSGIProcessGroup geonode
        WSGIApplicationGroup %{GLOBAL}
        WSGIPassAuthorization On
        WSGIScriptAlias / /opt/geonode_data/wsgi/geonode.wsgi

        ProxyPreserveHost On
        ProxyPass /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPassReverse /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPass /geonetwork http://localhost:8080/geonetwork
        ProxyPassReverse /geonetwork http://localhost:8080/geonetwork
     </VirtualHost>

   And then symlink it to the apache sites directory::

      $ sudo ln -s /opt/geonode_data/geonode.apache /etc/apache2/sites-available/geonode

10. Set the filesystem ownership to the Apache user for the geonode/htdocs and wsgi folders::

      $ sudo chown www-data -R /opt/geonode_data/{static,wsgi}

11. Disable the default site that comes with apache, enable the one just
    created, and activate the WSGI and HTTP Proxy modules for apache::

      $ sudo a2dissite default
      $ sudo a2enmod proxy_http wsgi
      $ sudo a2ensite geonode

12. Restart the web server to apply the new configuration::

      $ sudo /etc/init.d/apache2 restart

    You should now be able to browse through the static media files using your
    web browser.  You should be able to load the GeoNode header graphic from
    http://localhost/geonode-client/gn/theme/app/img/header-bg.png .

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

4. You should now be able to see the GeoNode site at http://localhost/
