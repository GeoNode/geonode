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

Python:

The Python interpreter in the CentOS repositories does not support GeoNode;
instead use the python26 package from the `EPEL
<http://fedoraproject.org/wiki/EPEL>`_ project.  Follow the instructions from
the wiki to activate the EPEL repository, then install Python with::

    $ # The command below is an example, please adjust based on your exact version of CentOS
    $ rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm
    $ yum install python26 python26-devel

Java:

You will also need a Java Runtime Environment (JRE).  We recommend following
the `Oracle installation instructions
<http://www.oracle.com/technetwork/java/javase/install-linux-self-extracting-142296.html>`_
While other JRE versions will work, Oracle's is recommended for performance
reasons.  For the purposes of this guide we will assume that the JRE is
installed to :file:`/opt/jre1.6.0_23/`

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

     JAVA_HOME=/opt/jre1.6.0_23

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

     $ cd /opt/apache-tomcat-6.0.29
     $ ./bin/catalina.sh start

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

2. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/opt/apache-tomcat-6.0.29/webapps/geoserver-geonode-dev/WEB-INF/web.xml` 
   and add a context-parameter::

     $ vim /var/lib/tomcat6/webapps/geoserver-geonode-dev/WEB-INF/web.xml

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>

.. note::

   If you have more than one website running in apache using http://localhost will not work.
   In that case you need to set explicitly the name of the virtual host, for example:
   http://geonode.mycompany.net


3. Move the GeoServer "data directory" outside of the servlet container to
   avoid having it overwritten on later upgrades::
 
     <context-param>
       <param-name>GEOSERVER_DATA_DIR</param-name>
       <param-value>/opt/geonode_data/geodata</param-value>
     </context-param>


   GeoServer requires a particular directory structure in data directories, so
   also copy the template datadir from the tomcat webapps directory::
 
      $ mkdir -p /opt/geonode_data/
      $ cp -R /opt/apache-tomcat-6.0.29/webapps/geoserver-geonode-dev/data/ /opt/geonode_data/geodata

 Changes after Tomcat is Running                                                                                         
-------------------------------

1. To restart tomcat::
  
     $ /opt/apache-tomcat-6.0.29/bin/catalina.sh stop && 
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

     $ yum install postgresql postgresql-server
     $ chkconfig postgresql on
     $ service postgresql restart

   Edit the ``pg_hba.conf`` file to use password based authentication, change
   `ident, sameuser` to `md5`::

     $ vim /var/lib/pgsql/data/pg_hba.conf

     # "local" is for Unix domain socket connections only
     local   all         all                               md5

   Then restart postgres in order to pick up the changes::

     $ service postgresql restart

2. Create geonode database and geonode user account (you will be prompted for a password)::

     $ su - postgres
     $ createdb geonode && createuser -s -P geonode
     $ exit

.. seealso:: 

    See the Django setup notes for instructions on creating the database tables
    for the GeoNode app.


Install GeoNode Django Site
---------------------------

1. Install required libraries::

     $ yum install gcc libjpeg-devel postgresql-devel libpng-devel

  psycopg2::

     $ cd /tmp
     $ wget http://initd.org/psycopg/tarballs/psycopg2-latest.tar.gz
     $ tar zxvf psycopg2-latest.tar.gz
     $ cd psycopg2-2.3.2/
     $ python26 setup.py install

  geos::

     $ wget http://download.osgeo.org/geos/geos-3.2.2.tar.bz2
     $ tar xjf geos-3.2.2.tar.bz2
     $ cd geos-3.2.2
     $ ./configure
     $ make
     $ make install
     $ cd ..

  proj4::

     $ wget http://download.osgeo.org/proj/proj-4.7.0.tar.gz
     $ wget http://download.osgeo.org/proj/proj-datumgrid-1.5.zip
     $ tar xzf proj-4.7.0.tar.gz
     $ cd proj-4.7.0/nad
     $ unzip ../../proj-datumgrid-1.5.zip
     $ cd ..
     $ ./configure
     $ make
     $ make install
     $ cd ..

  gdal::

     $ wget http://download.osgeo.org/gdal/gdal-1.7.3.tar.gz
     $ tar xzf gdal-1.7.3.tar.gz
     $ cd gdal-1.7.3
     $ ./configure --with-geotiff=internal --with-libtiff=internal
     $ make # Go get some coffee, this takes a while.
     $ make install
     $ cd ..

.. note::
    We need to disable the use of external tiff libraries in CentOS because it 
    gives a compilation error otherwise.

  Open `` /etc/ld.so.conf`` and add the following line::
    
     /usr/local/lib

  The run::

     $ ldconfig

2. Create new directories in ``/opt/geonode/`` for the geonode static files, uploads,
   and apache configuration (``static``, ``static/media``, ``wsgi``,
   respectively)::

     $ mkdir -p /opt/geonode_data/{static,static/media,wsgi}

3. Place the "static media" (aka JavaScript, CSS, and images) into the
   ``static`` directory::

     $ unzip /tmp/GeoNode-1.0/geonode-client.zip -d /opt/geonode_data/static/

4. Place the Python bundle and installer scripts into the ``/opt/geonode``
   directory::

     $ mkdir -p /opt/geonode
     $ cd /tmp/GeoNode-1.0/
     $ cp bootstrap.py geonode-webapp.pybundle pavement.py /opt/geonode/

5. Use the bootstrap script to set up a virtualenv sandbox and install Python
   dependencies::

     $ cd /opt/geonode/
     $ python26 bootstrap.py

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

     ln -s /opt/geonode_data/local_settings.py /opt/geonode/src/GeoNodePy/geonode/local_settings.py

.. note::

     The local_settings.py approach is a Django idiom to help customizing websites, it works because
     the last line of ``src/GeoNodePy/geonode/settings.py`` imports it if it exists. 

7. Place a wsgi launcher script in :file:`/opt/geonode_data/wsgi/geonode.wsgi` ::                                                        

     import os
     os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
     from django.core.handlers.wsgi import WSGIHandler
     application = WSGIHandler()


8. Install the httpd package::

     $ yum install httpd python26-mod_wsgi

.. note::
       The default CentOS package repository includes a ``mod_wsgi`` package
       which is distinct from the ``python26_mod_wsgi`` package provided by
       ELGIS.  Since GeoNode requires Python 2.6, it will not function with the
       default package, so please ensure that you install the package as listed
       above.

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

        ErrorLog /var/log/httpd/error.log

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        CustomLog /var/log/httpd/access.log combined

        Alias /geonode-client/ /opt/geonode_data/static/geonode-client/
        Alias /media/ /opt/geonode_data/static/media/
        Alias /admin-media/ /opt/geonode/lib/python2.6/site-packages/django/contrib/admin/media/

        WSGIProcessGroup geonode
        WSGIApplicationGroup %{GLOBAL}
        WSGIPassAuthorization On
        WSGIScriptAlias / /opt/geonode_data/wsgi/geonode.wsgi
        WSGISocketPrefix run/wsgi

        ProxyPreserveHost On
        ProxyPass /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPassReverse /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
        ProxyPass /geonetwork http://localhost:8080/geonetwork
        ProxyPassReverse /geonetwork http://localhost:8080/geonetwork
     </VirtualHost>

  And then symlink it to the apache sites directory::

      $ ln -s /opt/geonode_data/geonode.apache /etc/httpd/conf.d/geonode.conf


10. Set the filesystem ownership to the Apache user for the geonode_data static and wsgi folders::

      $ chown apache -R /opt/geonode_data/{static,wsgi}

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

.. note::
 
   If you have problems uploading files, please take enable the verbose logging
   http://docs.geonode.org/1.0/logging.html  
