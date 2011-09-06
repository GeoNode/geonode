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

You can also get the latest release from http://dev.geonode.org/release/ or
the `GeoNode project wiki <http://dev.geonode.org/trac/>`_ .
You can unpack it like::

    $ tar xvzf GeoNode-1.1.tar.gz
    GeoNode-1.1/geonetwork.war
    GeoNode-1.1/geonode-webapp.pybundle
    GeoNode-1.1/geoserver.war
    GeoNode-1.1/bootstrap.py
    GeoNode-1.1/deploy-libs.txt
    GeoNode-1.1/install.sh
    GeoNode-1.1/support/

This tarball comes with an install script and a directory with supporting config files.

Automatic installation
----------------------

Here are the steps to use the automated installer::

    sudo apt-get install python python-support python-dev python-virtualenv openjdk-6-jre tomcat6 postgresql-8.4 gcc patch zip  python-imaging python-reportlab gdal-bin libgeos-dev python-urlgrabber python-pastescript gettext postgresql-contrib postgresql-8.4-postgis,libpq-dev unzip libjpeg-dev libpng-dev python-gdal libproj-dev python-psycopg2 apache2 libapache2-mod-wsgi
    cd GeoNode-1.1/
    sudo ./install.sh support/config-ubuntu.sh

More instructions can be found in the README distributed with the release as well as the pointer to the documentation page about configuring GeoNode for production after it has been installed.

Manual Installation
===================

Here is the complete set of instructions to install GeoNode manually:

Runtimes
--------

Python::

  # apt-get install python python-dev

Java:

For Sun/Oracle Java (recommended for better rendering performance)::

  # vi /etc/apt/sources.list
  # <enable partners repository>
  # apt-get update
  # apt-get install sun-java6-jre

For OpenJDK (simpler install)::

  # apt-get install openjdk-6-jre

Servlet Container Installation
------------------------------

1. Install tomcat from ubuntu packages::

   # apt-get install tomcat6

2. Update JAVA_OPTS::

   # vi /etc/init.d/tomcat6
   # export JAVA_OPTS="-Xmx1024m -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement"

   .. note::

     The Java options used are as follows:

     * ``-Xmx1024m`` tells Java to use 1GB of RAM instead of the default value

     * ``-XX:MaxPermSize=256M`` increase the amount of space used for "permgen", needed to run geonetwork/geoserver.

     * ``-XX:CompileCommand=...`` is a workaround for a JVM bug that affect GeoNetwork; see http://trac.osgeo.org/geonetwork/ticket/301


3. Restart tomcat::
   
   # sudo /etc/init.d/tomcat6 restart

Deploying GeoNetwork
--------------------

1. Move :file:`geonetwork.war` from the GeoNode release archive into the Tomcat
   deployment directory::

     # sudo cp geonetwork.war /var/lib/tomcat6/webapps/ 

.. note:: 

     The GeoNetwork username and password both default to ``admin`` and
     should be changed, but they cannot be changed unless the server is running.
     See the instructions below for starting up Tomcat.

Deploying GeoServer
-------------------

1. Move :file:`geoserver.war` from the GeoNode release archive into
   the Tomcat deployment directory::

     # sudo cp geoserver.war /var/lib/tomcat6/webapps/

2. GeoServer uses the Django web application to authenticate users.  By
   default, it will look for GeoNode at http://localhost:8000/ but we will be
   running the Django application on http://localhost:80/ so we have to
   configure GeoServer to look at that URL.  To do so, edit
   :file:`/var/lib/tomcat6/webapps/geoserver/WEB-INF/web.xml` 
   and add a context-parameter::

     <context-param>
       <param-name>GEONODE_BASE_URL</param-name>
       <param-value>http://localhost/</param-value>
     </context-param>

3. Move the GeoServer "data directory" outside of the servlet container to
   avoid having it overwritten on later upgrades::

     <context-param>
       <param-name>GEOSERVER_DATA_DIR</param-name>
       <param-value>/opt/geoserver_data/</param-value>
     </context-param>

   GeoServer requires a particular directory structure in data directories, so
   also copy the template datadir from the tomcat webapps directory::

     # cp -R /var/lib/tomcat6/webapps/geoserver/data/ /opt/geoserver_data
     # chown tomcat6 -R /opt/geoserver_data/

4. Restart tomcat::

   # sudo /etc/init.d/tomcat6 restart

Changes after Tomcat is Running
-------------------------------

1. To start tomcat::

     # /etc/init.d/tomcat6 start

2. You should now be able to visit the GeoServer web interface at
   http://localhost:8080/geoserver/ .  GeoServer is configured to
   use the Django database for authentication, so you won't be able to log in
   to the GeoServer console until Django is up and running.

3. The GeoNetwork administrative account will be using the default password.  You
   should navigate to `the GeoNetwork web interface
   <http://localhost:8080/geonetwork/>`_ and change the password for this account,
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
    configuration, is stored inside of ``[tomcat]/webapps/geonetwork/`` .  This
    directory can be copied between machines to quickly reproduce a
    configuration with a given administrative password across multiple
    machines.

Set up PostgreSQL
-----------------

1. Install the postgresql package::

     # apt-get install postgresql-8.4

2. Create geonode database and geonode user account (you will be prompted for a password)::

     # su - postgres
     $ createdb geonode && createuser -s -P geonode

.. seealso:: 

    See the Django setup notes for instructions on creating the database tables
    for the GeoNode app.

Install GeoNode Django Site
---------------------------

1. Install required libraries::

     # apt-get install gcc libjpeg-dev libpng-dev python-gdal python-psycopg2 libproj-dev proj-bin proj-data


2. Place the Python bundle and installer scripts into the ``/var/lib/geonode``
   directory::

    # mkdir -p /var/lib/geonode/
    # cp bootstrap.py geonode-webapp.pybundle /var/lib/geonode/

3. Use the bootstrap script to set up a virtualenv sandbox and install Python
   dependencies::

     # cd /var/lib/geonode/
     # python bootstrap.py


4. Create new directories in ``/var/www/geonode`` for the geonode static files, uploads,
   and python scripts (``static``, ``uploads``, ``wsgi``,
   respectively)::

    # mkdir -p /var/www/geonode/{static,uploads,wsgi}



5. Configure the ``local_settings.py``  using the one provided in the ``support`` directory with the release as the base::

    # mkdir -p /etc/geonode
    # cp support/geonode.local_settings /etc/geonode
    # ln -s /etc/geonode/local_settings.py /var/lib/geonode/src/GeoNodePy/geonode/local_settings.py

6. Copy the wsgi launcher script in the ``support`` folder to ``/var/www/geonode/wsgi/geonode.wsgi``::

    # cp support/geonode.wsgi /var/www/geonode/wsgi/geonode.wsgi


7. Install the httpd package::

    # apt-get install apache2 libapache2-mod-wsgi

8. Copy the apache configuration file to the apache dir::

    # cp support/geonode.apache /etc/apache2/sites-available/geonode

   And put the correct path to your virtualenv site-packages dir in the first line ``/var/lib/geonode/lib/python2.6/site-packages`` it will depend on the version of Python you are using.
   

9. Set the filesystem ownership to the Apache user for the ``geonode`` folder::

      # chown www-data -R /var/www/geonode/
      # chown www-data -R /var/lib/geonode/

10. Disable the default site that comes with apache, enable the one just
    created, and activate the WSGI and HTTP Proxy modules for apache::

      # a2dissite default
      # a2enmod proxy_http wsgi
      # a2ensite geonode

11. Restart the web server to apply the new configuration::

      # /etc/init.d/apache2 restart

    You should now be able to browse through the static media files using your
    web browser.  You should be able to load the GeoNode header graphic from
    http://localhost/media/static/gn/theme/app/img/header-bg.png .

12. Set up the database tables using the Django admin tool (you will be
    prompted for an admin username and account)::

      # /var/lib/geonode/bin/django-admin.py syncdb --settings=geonode.settings

13. You should now be able to see the GeoNode site at http://localhost/


.. note::

 If you have problems uploading files, please enable the verbose logging
 http://docs.geonode.org/1.1/logging.html

