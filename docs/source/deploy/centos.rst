Deploying on CentOS 5
=====================

This page provides a guide to installing GeoNode on the CentOS Linux
distribution.  

.. note:: 

    While we intend to provide a detailed, accurate explanation of the
    installation process, it may become out of date.  If you run into problems
    with the process described in this document, please don't hesitate to let
    the GeoNode team know so we can keep it up to date.

.. note::
    
    Disabling SELinux http://www.centos.org/docs/5/html/5.2/Deployment_Guide/sec-sel-enable-disable.html

The stack used is:

* *Servlet Container*: Apache Tomcat

* *Static File Server*: Apache httpd

* *Python/WSGI Container*: mod_wsgi

* *Django Database*: Postgres 

Download GeoNode Release Archive
--------------------------------
Release archives of GeoNode are produced from the GeoNode sources using::

  $ paver make_release # from the root of a working dir

You can also get the latest release from http://dev.geonode.org/release/ or 
the `GeoNode project wiki <http://dev.geonode.org/trac/>`_ .  
You can unpack it like::

  $ tar xvzf GeoNode-1.0.1.tar.gz
  GeoNode-1.0.1/geonetwork.war
  GeoNode-1.0.1/pavement.py
  GeoNode-1.0.1/geonode-webapp.pybundle
  GeoNode-1.0.1/geoserver-geonode-dev.war
  GeoNode-1.0.1/bootstrap.py
  GeoNode-1.0.1/deploy-libs.txt
  GeoNode-1.0.1/deploy.ini.ex

Install Dependencies
--------------------

1. Add Additional Repositories

     The Python interpreter in the CentOS repositories does not support GeoNode;
     instead use the python26 package from the `EPEL
     <http://fedoraproject.org/wiki/EPEL>`_ project.  Follow the instructions from
     the wiki to activate the EPEL repository::

     $ # The command below is an example, please adjust based on your exact version of CentOS
     $ su -c 'rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm'

     Enable the `ELGIS testing repository
     <http://wiki.osgeo.org/wiki/Enterprise_Linux_GIS>`_::

     $ # The command below is an example, please adjust based on your exact version of CentOS
     $ su -c 'rpm -Uvh http://elgis.argeo.org/repos/5/elgis-release-5-5_0.noarch.rpm'

2. Install Java Runtime

     You will need a Java Runtime Environment (JRE).  We recommend following
     the `Oracle installation instructions
     <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_
     While other JRE versions will work, Oracle's is recommended for performance
     reasons.  

3. Install Dependencies with yum::

    $ su -c 'yum install python26 python26-devel tomcat5 httpd python-virtualenv python26-mod_wsgi postgresql84 postgresql84-server gcc postgresql84-python postgresql84-libs postgresql84-devel python26-devel geos'


Tomcat Servlet Container Configuration
--------------------------------------

Tomcat Servlet container was already installed with yum in previous step

1. Add additional java options to the Tomcat startup settings 
   Edit the file :file:`/etc/sysconfig/tomcat5` and add the following.::

    JAVA_OPTS="-Xmx1024m -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement"
  
    .. note::
 
      The Java options used are as follows: 
      * ``-Xmx1024m`` tells Java to use 1GB of RAM instead of the default value
      * ``-XX:MaxPermSize=256M`` increase the amount of space used for
        "permgen", needed to run geonetwork/geoserver.
      * ``-XX:CompileCommand=...`` is a workaround for a JVM bug that affects
        GeoNetwork; see http://trac.osgeo.org/geonetwork/ticket/301

2. Set tomcat to start on boot:: 
   
    $ chkconfig tomcat5 on

3. Start Tomcat::

    $ service tomcat5 start


Deploying GeoNetwork
--------------------

1. Move :file:`geonetwork.war` from the GeoNode release archive into the Tomcat
   deployment directory::

     $ mv GeoNode-1.0.1/geonetwork.war /var/lib/tomcat5/webapps/ 

2. The GeoNetwork administrative account will be using the default password.  You
   should navigate to `the GeoNetwork web interface
   <http://localhost:8080/geonetwork/>` and change the password for this account,
   taking note of the new password for later use. (Log in with the username
   ``admin`` and password ``admin``, then use the "Administration" link in the
   top navigation menu to change the password.)

3. (optional but recommended) GeoNetwork's default configuration includes
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

Deploying GeoServer
-------------------

1. Move :file:`geoserver-geonode-dev.war` from the GeoNode release archive into
   the Tomcat deployment directory::

     $ mv GeoNode-1.0.1/geoserver-geonode-dev.war /var/lib/tomcat5/webapps/

2. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/var/lib/tomcat5/webapps/geoserver-geonode-dev/WEB-INF/web.xml` 
   and add a context-parameter::

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>

.. note::

   If you have more than one website running in apache, using ``http://localhost/`` will not work.
   In that case you need to set explicitly the name of the virtual host, for example:
   http://geonode.mycompany.net/

3. Move the GeoServer "data directory" outside of the servlet container to
   avoid having it overwritten on later upgrades. Edit the file
   :file`/var/lib/tomcat5/webapps/geoserver-geonode-dev/WEB-INF/web.xml`
   by uncommenting the block below and setting the param-value to 
   /opt/geoserver_data::

     <context-param>
        <param-name>GEOSERVER_DATA_DIR</param-name>
        <param-value>/opt/geoserver_data</param-value>
     </context-param>

4. GeoServer requires a particular directory structure in data directories, so 
   also copy the template datadir from the tomcat webapps directory::
   
     $ cp -rp /var/lib/tomcat5/webapps/geoserver-geonode-dev/data/* /opt/geoserver_data/.
     $ chown tomcat. /opt/geoserver_data/ -R

4. After modifying ``web.xml`` you will need to restart Tomcat for changes to
   take effect::

     $ service tomcat5 restart

5. You should now be able to visit the GeoServer web interface at
   http://localhost:8080/geoserver-geonode-dev/ . 
   
.. note::

     GeoServer is configured to use the Django database for authentication, 
     so you won't be able to log in to the GeoServer console until Django 
     is up and running.

Configuring Apache httpd
------------------------

The Apache httpd server was installed with yum in previous step. Some changes to 
its configuration are necessary.

1. Create a new directory :file:`/var/www/geonode` to contain the GeoNode
   web application files, including a subdirectory for 'media' such as CSS
   stylesheets and JavaScript scripts::

     $ mkdir -p /var/www/geonode/{htdocs,htdocs/media,wsgi/geonode/}

2. Create a new configuration file in :file:`/etc/httpd/conf.d/geonode.conf` ::

     DocumentRoot "/var/www/geonode/htdocs"

     <Directory "/var/www/geonode/htdocs">
        AllowOverride None
        Order allow,deny
        Allow from all
     </Directory>

     <Proxy *>
        Order allow,deny
        Allow from all
     </Proxy>

     LogLevel debug

     ProxyPreserveHost On

     ProxyPass /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
     ProxyPassReverse /geoserver-geonode-dev http://localhost:8080/geoserver-geonode-dev
     ProxyPass /geonetwork http://localhost:8080/geonetwork
     ProxyPassReverse /geonetwork http://localhost:8080/geonetwork

3. Start up the web server::

     $ service httpd start

4. Set the web server to start on boot::

     $ chkconfig tomcat5 on 

5. You should now be able to browse the http server and verify that the proxied tomcat
   services are working properly::

     http://localhost/geonetwork/
     http://localhost/geoserver-geonode-dev/

Installing the GeoNode Django Application
-----------------------------------------

1. Copy GeoNode release files to application directory::

     $ cp GeoNode-1.0.1/bootstrap.py /var/www/geonode/wsgi/geonode/.
     $ cp GeoNode-1.0.1/geonode-webapp.pybundle /var/www/geonode/wsgi/geonode/.
     $ cp GeoNode-1.0.1/pavement.py /var/www/geonode/wsgi/geonode/.

2. Run the bootstrap script to set up a virtualenv sandbox and install Python
   dependencies:: 

     $ cd /var/www/geonode/wsgi/geonode
     $ python26 bootstrap.py

3. Install required psycopg2 dependency::

     $ cd /var/www/geonode/wsgi/geonode
     $ source bin/activate
     $ pip install http://initd.org/psycopg/tarballs/PSYCOPG-2-2/psycopg2-2.2.0.tar.gz

4. Create a Local Settings Python file at
   :file:`/var/www/geonode/wsgi/geonode/src/GeoNodePy/geonode/local_settings.py` to
   contain settings for the local server. for example:: 

     DEBUG = TEMPLATE_DEBUG = False
     MINIFIED_RESOURCES = True
     SERVE_MEDIA=False

     SITENAME = "GeoNode"
     SITEURL = "http://localhost/"

     DATABASE_ENGINE = 'postgresql_psycopg2'
     DATABASE_NAME = 'geonode'
     DATABASE_USER = 'geonode'
     DATABASE_PASSWORD = "geonode"
     DATABASE_HOST = 'localhost'
     DATABASE_PORT = '5432'

     LANGUAGE_CODE = 'en'

     # the filesystem path where uploaded data should be saved
     MEDIA_ROOT = "/var/www/geonode/htdocs/media/"

     # the web url to get to those saved files
     MEDIA_URL = SITEURL + "media/"

     GEONODE_UPLOAD_PATH = "/var/www/geonode/htdocs/media/"

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

     ADMIN_MEDIA_PREFIX="/admin-media/"

     DEFAULT_LAYERS_OWNER='admin'
     GEONODE_CLIENT_LOCATION = SITEURL + 'media/static/'

     import logging, sys
     for _module in ["geonode.maps.views", "geonode.maps.gs_helpers"]:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler(sys.stderr))
        _logger.setLevel(logging.DEBUG)

.. note::

     The local_settings.py approach is a Django idiom to help customizing websites, it works because
     the last line of ``src/GeoNodePy/geonode/settings.py`` imports it if it exists.

Installing and Configuring mod_wsgi
-----------------------------------

1. Create a short Python script in :file:`/var/www/geonode/wsgi/geonode.wsgi` to load
   the GeoNode application in Apache::

     #! /var/www/geonode/wsgi/geonode.wsgi 
     import site, os
     site.addsitedir('/var/www/geonode/wsgi/geonode/lib/python2.6/site-packages')
     os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
     from django.core.handlers.wsgi import WSGIHandler
     application = WSGIHandler()

2. Edit the configuration file :file:`/etc/httpd/conf.d/geonode.conf` that was
   created earlier and add on to the end::

     Alias /media "/var/www/geonode/wsgi/geonode/src/GeoNodePy/geonode/media"
     Alias /admin-media/ /var/www/geonode/wsgi/geonode/lib/python2.6/site-packages/django/contrib/admin/media/
     
     WSGIDaemonProcess geonode python-path=/var/www/geonode/wsgi/geonode/lib/python2.6/site-packages
     WSGIScriptAlias / /var/www/geonode/wsgi/geonode.wsgi 
     WSGISocketPrefix /var/run/wsgi
     WSGIPassAuthorization On

3. Now restart the webserver::

     $ service httpd restart

   .. note:: 

     The GeoNode site won't be working just yet; you still need to
     initialize the database before it will work.

Prepare the Django database
---------------------------

1. Initialize postgres and set it to start on boot:: 

    $ service postgresql initdb
    $ service postgresql start
    $ chkconfig postgresql on 

2. Create geonode database and geonode user account (you will be prompted for a password)::

    $ su - postgres
    $ createdb geonode && createuser -s -P geonode 
    $ exit

3. Edit the ``pg_hba.conf`` file to use password based authentication, change
   `ident, sameuser` to `md5`::

     $ vim /var/lib/pgsql/data/pg_hba.conf

     host   all         all                               md5

     Then restart postgres in order to pick up the changes::

     $ service postgresql restart

4. Activate the GeoNode virtualenv if it is not already active::

     $ cd /var/www/geonode/wsgi/geonode
     $ source bin/activate

5. Use the `django-admin` tool to initialize the database::

     $ django-admin.py syncdb --settings=geonode.settings

   This command should request a user name and password from you; these will be
   used for an admin account on the GeoNode site.

6. Use `django-admin` again to synchronize GeoServer, GeoNode, and GeoNetwork::
    
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

7. You should now be able to see the GeoNode site at http://localhost/

.. note::
    
    If you have problems uploading files, please enable the verbose logging
    http://docs.geonode.org/1.0/logging.html


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
