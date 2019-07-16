============
GeoNode Core
============

Overview
========

The following steps will guide you to a fresh setup of GeoNode. All guides will first install and configure the system to run it in ``DEBUG`` mode (also known as ``DEVELOPMENT`` mode) and then by configuring an HTTPD server to serve GeoNode through the standard ``HTTP`` (``80``) port.

Those guides **are not** meant to be used on a production system. There will be dedicated chapters that will show you some *hints* to optimize GeoNode for a production-ready machine. In any case, we strongly suggest to task an experienced *DevOp* or *System Administrator* before exposing your server to the ``WEB``.

Ubuntu 18.04
============

This part of the documentation describes the complete setup process for GeoNode on an Ubuntu 18.04 64-bit clean environment (Desktop or Server). All examples use shell commands that you must enter on a local terminal or a remote shell.
- If you have a graphical desktop environment you can open the terminal application after login;
- if you are working on a remote server the provider or sysadmin should has given you access through an ssh client.

.. _install_dep:

Install the dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

In this section, we are going to install all the basic packages and tools needed for a complete GeoNode installation. To follow this guide, a basic knowledge about Ubuntu Server configuration and working with a shell is required. This guide uses ``vim`` as the editor; fill free to use ``nano``, ``gedit`` or others.

Upgrade system packages
.......................

Check that your system is already up-to-date with the repository running the following commands:

.. code-block:: shell

   sudo apt update
   sudo apt upgrade


Packages Installation
.....................

We will use **example.org** as fictitious Domain Name.

First, we are going to install all the **system packages** needed for the GeoNode setup. Login to the target machine and execute the following commands:

.. code-block:: shell

  # Install packages from GeoNode core
  sudo apt install -y python-gdal gdal-bin
  sudo apt install -y python-pip python-dev python-virtualenv virtualenvwrapper
  sudo apt install -y libxml2 libxml2-dev gettext
  sudo apt install -y libxslt1-dev libjpeg-dev libpng-dev libpq-dev libgdal-dev libgdal20
  sudo apt install -y software-properties-common build-essential
  sudo apt install -y git unzip gcc zlib1g-dev libgeos-dev libproj-dev
  sudo apt install -y sqlite3 spatialite-bin libsqlite3-mod-spatialite

  # Install Openjdk
  sudo -i apt update
  sudo apt install openjdk-8-jdk-headless default-jdk-headless -y
  sudo update-java-alternatives --jre-headless --jre --set java-1.8.0-openjdk-amd64

  # Install VIM
  sudo apt install -y vim

  sudo apt update -y
  sudo apt upgrade -y
  sudo apt autoremove -y
  sudo apt autoclean -y
  sudo apt purge -y
  sudo apt clean -y

Create a Dedicated User
.......................

In the following steps a User named ``geonode`` is created (if needed) and used: to run installation commands the user must be in the ``sudo`` group.

Create User ``geonode`` **if not present**:

.. code-block:: shell

  # Follow the prompts to set the new user's information.
  # It is fine to accept the defaults to leave all of this information blank.
  sudo adduser geonode

  # The following command adds the user geonode to group sudo
  sudo usermod -aG sudo geonode

  # make sure the newly created user is allowed to login by ssh
  # (out of the scope of this documentation) and switch to User geonode
  su geonode

GeoNode Installation
^^^^^^^^^^^^^^^^^^^^

This is the most basic installation of GeoNode. It won't use any external server like ``Apache Tomcat``, ``PostgreSQL`` or ``HTTPD``.

It will run locally against a file-system based ``SQLite`` database.


First of all we need to prepare a new Python Virtual Environment

Since geonode needs a large number of different python libraries and packages, it's recommended to use a python virtual environment to avoid conflicts on dependencies with system wide python packages and other installed software. See also documentation of `Virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/stable/>`_ package for more information

.. code-block:: shell

  # Create the GeoNode Virtual Environment (first time only)
  mkvirtualenv --no-site-packages geonode

At this point your command prompt shows a ``(geonode)`` prefix, this indicates that your virtualenv is active.

.. note:: The next time you need to access the Virtual Environment just run

  .. code-block:: shell

    workon geonode


.. code-block:: shell

  # Let's create the GeoNode core base folder and clone it
  sudo mkdir -p /opt/geonode/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode/
  sudo chmod -Rf 775 /opt/geonode/

  # Clone the GeoNode source code on /opt/geonode
  cd /opt
  git clone https://github.com/GeoNode/geonode.git geonode

  # Install the Python packages
  cd /opt/geonode
  pip install -r requirements.txt --upgrade --no-cache --no-cache-dir
  pip install -e . --upgrade --no-cache --no-cache-dir

  # Install GDAL Utilities for Python
  pip install pygdal=="`gdal-config --version`.*"

Run GeoNode for the first time in DEBUG Mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

  Be sure you have successfully completed all the steps of the section :ref:`install_dep`.

This command will run both GeoNode and GeoServer locally after having prepared the SQLite database. The server will start in ``DEBUG`` (or ``DEVELOPMENT``) mode, and it will start the following services:

#. GeoNode on ``http://localhost:8000/``
#. GeoServer on ``http://localhost:8080/geoserver/``

This modality is beneficial to debug issues and/or develop new features, but it cannot be used on a production system.

.. code-block:: shell

  # Prepare the GeoNode SQLite database (the first time only)
  paver setup
  paver sync

.. note::

  In case you want to start again from a clean situation, just run

  .. code:: shell

    paver reset_hard

.. warning:: This will blow up completely your ``local_settings``, delete the SQLlite database and remove the GeoServer data dir.

.. code-block:: shell

  # Run the server in DEBUG mode
  paver start

Once the server has finished the initialization and prints on the console the sentence ``GeoNode is now available.``, you can open a browser and go to::

  http://localhost:8000/

Sign-in with::

  user: admin
  password: admin

.. _configure_dbs_core:

Postgis database Setup
^^^^^^^^^^^^^^^^^^^^^^

.. warning::

  Be sure you have successfully completed all the steps of the section :ref:`install_dep`.

In this section, we are going to setup users and databases for GeoNode in PostgreSQL.

Install and Configure the PostgreSQL Database System
....................................................

In this section we are going to install the ``PostgreSQL`` packages along with the ``PostGIS`` extension. Those steps must be done **only** if you don't have the DB already installed on your system.

.. code-block:: shell

  sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
  sudo wget --no-check-certificate --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

  sudo apt update
  sudo apt install -y postgresql-11 postgresql-11-postgis-2.5 postgresql-11-postgis-2.5-scripts postgresql-contrib-11 postgresql-client-11

We now must create two databases, ``geonode`` and ``geonode_data``, belonging to the role ``geonode``.

.. note:: This is our default configuration. You can use any database or role you need. The connection parameters must be correctly configured on ``settings``, as we will see later in this section.

Databases and Permissions
.........................

First, create the geonode user. GeoNode is going to use this user to access the database

.. code-block:: shell

  sudo -u postgres createuser -P geonode

You will be prompted asked to set a password for the user. Enter ``geonode`` as password.

.. warning:: This is a sample password used for the sake of simplicity. This password is very **weak** and should be changed in a production environment.

Create database ``geonode`` and ``geonode_data`` with owner ``geonode``

.. code-block:: shell

  sudo -u postgres createdb -O geonode geonode
  sudo -u postgres createdb -O geonode geonode_data

Next let's create PostGIS extensions

.. code-block:: shell

  sudo -u postgres psql -d geonode_data -c 'CREATE EXTENSION postgis;'
  sudo -u postgres psql -d geonode_data -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
  sudo -u postgres psql -d geonode_data -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
  sudo -u postgres psql -d geonode_data -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO geonode;'

Final step is to change user access policies for local connections in the file ``pg_hba.conf``

.. code-block:: shell

  sudo vim /etc/postgresql/11/main/pg_hba.conf

Scroll down to the bottom of the document. We only need to edit one line.

.. code-block:: shell

  # "local" is for Unix domain socket connections only
  # local   all             all                                     peer
  local   all             all                                     trust

.. warning:: If your ``PostgreSQL`` database resides on a **separate/remote machine**, you'll have to **allow** remote access to the databases in the ``/etc/postgresql/11/main/pg_hba.conf`` to the ``geonode`` user and tell PostgreSQL to **accept** non-local connections in your ``/etc/postgresql/11/main/postgresql.conf`` file

Restart PostgreSQL to make the change effective.

.. code-block:: shell

  sudo service postgresql restart

PostgreSQL is now ready. To test the configuration, try to connect to the ``geonode`` database as ``geonode`` role.

.. code-block:: shell

  psql -U geonode geonode
  \q


Install GeoServer
^^^^^^^^^^^^^^^^^

When running the command ``paver start``, as we have seen before, the script runs automatically a ``Jetty`` Servlet Java container running ``GeoServer`` with the default settings.

.. warning:: Before executing the next steps, be sure ``GeoNode`` and ``GeoServer`` paver services have been stopped. In order to do that

  .. code-block:: shell

    workon geonode
    cd /opt/geonode/
    paver stop

This is not the optimal way to run ``GeoServer``. This is a fundamental component of ``GeoNode`` and we must be sure it is running on a stable and reliable manner.

In this section, we are going to install the ``Apache Tomcat 8`` Servlet Java container, which will be started by default on the internal port ``8080``.

We will also perform several optimizations to:

1. Correctly setup the Java VM Options, like the available heap memory and the garbage collector options.
2. Externalize the ``GeoServer`` and ``GeoWebcache`` catalogs in order to allow further updates without the risk of deleting our datasets.

.. note:: This is still a basic setup of those components. More details will be provided on sections of the documentation concerning the hardening of the system in a production environment. Nevertheless, you will need to tweak a bit those settings accordingly with your current system. As an instance, if your machine does not have enough memory, you will need to lower down the initial amount of available heap memory. **Warnings** and **notes** will be placed below the statements that will require your attention.

.. code-block:: shell

  # Install Openjdk
  sudo -i apt update
  sudo apt install openjdk-8-jdk-headless default-jdk-headless -y
  sudo update-java-alternatives --jre-headless --jre --set java-1.8.0-openjdk-amd64

  # Check Java version
  java -version
    openjdk version "1.8.0_212"
    OpenJDK Runtime Environment (build 1.8.0_212-8u212-b03-0ubuntu1.18.04.1-b03)
    OpenJDK 64-Bit Server VM (build 25.212-b03, mixed mode)

  # Install Apache Tomcat 8
  sudo wget http://www-us.apache.org/dist/tomcat/tomcat-8/v8.5.41/bin/apache-tomcat-8.5.41.tar.gz
  sudo tar xzf apache-tomcat-8.5.41.tar.gz
  sudo mv apache-tomcat-8.5.41 /usr/local/apache-tomcat8
  sudo useradd -m -U -s /bin/false tomcat
  sudo usermod -a -G www-data tomcat
  sudo sed -i -e 's/xom-\*\.jar/xom-\*\.jar,bcprov\*\.jar/g' /usr/local/apache-tomcat8/conf/catalina.properties

  export JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:bin/java::")
  echo 'JAVA_HOME='$JAVA_HOME | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh

  # Add Tomcat user to www-data group !important!
  sudo usermod -a -G www-data tomcat

  sudo sh -c 'chmod +x /usr/local/apache-tomcat8/bin/*.sh'
  sudo chown -Rf tomcat:www-data /usr/local/apache-tomcat8

Let's create a system service to manage tomcat startup

.. code-block:: shell

  sudo vim /etc/systemd/system/tomcat.service

.. code-block:: shell

  [Unit]
  Description=Tomcat 8.5 servlet container
  After=network.target

  [Service]
  Type=forking

  User=tomcat
  Group=tomcat

  Environment="JAVA_HOME=/usr/lib/jvm/default-java"
  Environment="JAVA_OPTS=-Djava.security.egd=file:///dev/urandom"

  Environment="CATALINA_BASE=/usr/local/apache-tomcat8"
  Environment="CATALINA_HOME=/usr/local/apache-tomcat8"
  Environment="CATALINA_PID=/usr/local/apache-tomcat8/temp/tomcat.pid"

  ExecStart=/usr/local/apache-tomcat8/bin/startup.sh
  ExecStop=/usr/local/apache-tomcat8/bin/shutdown.sh

  [Install]
  WantedBy=multi-user.target

To test the service:

.. code-block:: shell

  sudo systemctl daemon-reload
  sudo systemctl restart tomcat
  sudo systemctl status tomcat.service

To make it enabled by default

.. code-block:: shell

  sudo systemctl enable tomcat

GeoServer Optimizations
.......................

Let's externalize the ``GEOSERVER_DATA_DIR`` and ``logs``

.. code-block:: shell

  # Create the target folders
  sudo mkdir -p /opt/data
  sudo chown -Rf geonode:www-data /opt/data
  sudo chmod -Rf 775 /opt/data
  sudo mkdir -p /opt/data/logs
  sudo chown -Rf geonode:www-data /opt/data/logs
  sudo chmod -Rf 775 /opt/data/logs

  # Download and extract the default GEOSERVER_DATA_DIR
  sudo wget --no-check-certificate https://build.geo-solutions.it/geonode/geoserver/latest/data-2.14.3.zip
  sudo unzip data-2.14.3.zip -d /opt/data/

  sudo mv /opt/data/data/ /opt/data/geoserver_data
  sudo chown -Rf tomcat:www-data /opt/data/geoserver_data
  sudo chmod -Rf 775 /opt/data/geoserver_data

  sudo mkdir -p /opt/data/geoserver_logs
  sudo chown -Rf tomcat:www-data /opt/data/geoserver_logs
  sudo chmod -Rf 775 /opt/data/geoserver_logs

  sudo mkdir -p /opt/data/gwc_cache_dir
  sudo chown -Rf tomcat:www-data /opt/data/gwc_cache_dir
  sudo chmod -Rf 775 /opt/data/gwc_cache_dir

  # Download and install GeoServer
  sudo wget --no-check-certificate https://build.geo-solutions.it/geonode/geoserver/latest/geoserver-2.14.3.war
  sudo mv geoserver-2.14.3.war /usr/local/apache-tomcat8/webapps/geoserver.war

Let's now configure the ``JAVA_OPTS``, i.e. the parameters to run the Servlet Container, like heap memory, garbage collector and so on.

.. code-block:: shell

  sudo sed -i -e "s/JAVA_OPTS=/#JAVA_OPTS=/g" /usr/local/apache-tomcat8/bin/setenv.sh

  echo 'GEOSERVER_DATA_DIR="/opt/data/geoserver_data"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh
  echo 'GEOSERVER_LOG_LOCATION="/opt/data/geoserver_logs/geoserver.log"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh
  echo 'GEOWEBCACHE_CACHE_DIR="/opt/data/gwc_cache_dir"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh
  echo 'GEOFENCE_DIR="$GEOSERVER_DATA_DIR/geofence"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh
  echo 'TIMEZONE="UTC"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh

  echo 'JAVA_OPTS="-server -Djava.awt.headless=true -Dorg.geotools.shapefile.datetime=true -XX:+UseParallelGC -XX:ParallelGCThreads=4 -Dfile.encoding=UTF8 -Duser.timezone=$TIMEZONE -Xms512m -Xmx4096m -Djavax.servlet.request.encoding=UTF-8 -Djavax.servlet.response.encoding=UTF-8 -DGEOSERVER_DATA_DIR=$GEOSERVER_DATA_DIR -Dgeofence.dir=$GEOFENCE_DIR -DGEOSERVER_LOG_LOCATION=$GEOSERVER_LOG_LOCATION -DGEOWEBCACHE_CACHE_DIR=$GEOWEBCACHE_CACHE_DIR"' | sudo tee --append /usr/local/apache-tomcat8/bin/setenv.sh

.. note:: After the execution of the above statements, you should be able to see the new options written at the bottom of the file ``/usr/local/apache-tomcat8/bin/setenv.sh``.

  .. code-block:: shell

      ...
      # If you run Tomcat on port numbers that are all higher than 1023, then you
      # do not need authbind.  It is used for binding Tomcat to lower port numbers.
      # (yes/no, default: no)
      #AUTHBIND=no
      JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre/
      GEOSERVER_DATA_DIR="/opt/data/geoserver_data"
      GEOSERVER_LOG_LOCATION="/opt/data/geoserver_logs/geoserver.log"
      GEOWEBCACHE_CACHE_DIR="/opt/data/gwc_cache_dir"
      GEOFENCE_DIR="$GEOSERVER_DATA_DIR/geofence"
      TIMEZONE="UTC"
      JAVA_OPTS="-server -Djava.awt.headless=true -Dorg.geotools.shapefile.datetime=true -XX:+UseParallelGC -XX:ParallelGCThreads=4 -Dfile.encoding=UTF8 -Duser.timezone=$TIMEZONE -Xms512m -Xmx4096m -Djavax.servlet.request.encoding=UTF-8 -Djavax.servlet.response.encoding=UTF-8 -DGEOSERVER_DATA_DIR=$GEOSERVER_DATA_DIR -Dgeofence.dir=$GEOFENCE_DIR -DGEOSERVER_LOG_LOCATION=$GEOSERVER_LOG_LOCATION -DGEOWEBCACHE_CACHE_DIR=$GEOWEBCACHE_CACHE_DIR"

  Those options could be updated or changed manually at any time, accordingly to your needs.

.. warning:: The default options we are going to add to the Servlet Container, assume you can reserve at least ``4GB`` of ``RAM`` to ``GeoServer`` (see the option ``-Xmx4096m``). You must be sure your machine has enough memory to run both ``GeoServer`` and ``GeoNode``, which in this case means at least ``4GB`` for ``GeoServer`` plus at least ``2GB`` for ``GeoNode``. A total of at least ``6GB`` of ``RAM`` available on your machine. If you don't have enough ``RAM`` available, you can lower down the values ``-Xms512m -Xmx4096m``. Consider that with less ``RAM`` available, the performances of your services will be highly impacted.

In order to make the changes effective, you'll need to restart the Servlet Container.

.. code-block:: shell

  # Restart the server
  sudo systemctl daemon-reload
  sudo systemctl restart tomcat
  sudo systemctl status tomcat.service

  # Follow the startup logs
  sudo tail -F -n 300 /opt/data/geoserver_logs/geoserver.log

If you can see on the logs something similar to this, without errors

.. code-block:: shell

  ...
  2019-05-31 10:06:34,190 INFO [geoserver.wps] - Found 5 bindable processes in GeoServer specific processes
  2019-05-31 10:06:34,281 INFO [geoserver.wps] - Found 89 bindable processes in Deprecated processes
  2019-05-31 10:06:34,298 INFO [geoserver.wps] - Found 31 bindable processes in Vector processes
  2019-05-31 10:06:34,307 INFO [geoserver.wps] - Found 48 bindable processes in Geometry processes
  2019-05-31 10:06:34,307 INFO [geoserver.wps] - Found 1 bindable processes in PolygonLabelProcess
  2019-05-31 10:06:34,311 INFO [geoserver.wps] - Blacklisting process ras:ConvolveCoverage as the input kernel of type class javax.media.jai.KernelJAI cannot be handled
  2019-05-31 10:06:34,319 INFO [geoserver.wps] - Blacklisting process ras:RasterZonalStatistics2 as the input zones of type class java.lang.Object cannot be handled
  2019-05-31 10:06:34,320 INFO [geoserver.wps] - Blacklisting process ras:RasterZonalStatistics2 as the input nodata of type class it.geosolutions.jaiext.range.Range cannot be handled
  2019-05-31 10:06:34,320 INFO [geoserver.wps] - Blacklisting process ras:RasterZonalStatistics2 as the input rangeData of type class java.lang.Object cannot be handled
  2019-05-31 10:06:34,320 INFO [geoserver.wps] - Blacklisting process ras:RasterZonalStatistics2 as the output zonal statistics of type interface java.util.List cannot be handled
  2019-05-31 10:06:34,321 INFO [geoserver.wps] - Found 18 bindable processes in Raster processes
  2019-05-31 10:06:34,917 INFO [ows.OWSHandlerMapping] - Mapped URL path [/TestWfsPost] onto handler 'wfsTestServlet'
  2019-05-31 10:06:34,918 INFO [ows.OWSHandlerMapping] - Mapped URL path [/wfs/*] onto handler 'dispatcher'
  2019-05-31 10:06:34,918 INFO [ows.OWSHandlerMapping] - Mapped URL path [/wfs] onto handler 'dispatcher'
  2019-05-31 10:06:42,237 INFO [geoserver.security] - Start reloading user/groups for service named default
  2019-05-31 10:06:42,241 INFO [geoserver.security] - Reloading user/groups successful for service named default
  2019-05-31 10:06:42,357 WARN [auth.GeoFenceAuthenticationProvider] - INIT FROM CONFIG
  2019-05-31 10:06:42,494 INFO [geoserver.security] - AuthenticationCache Initialized with 1000 Max Entries, 300 seconds idle time, 600 seconds time to live and 3 concurrency level
  2019-05-31 10:06:42,495 INFO [geoserver.security] - AuthenticationCache Eviction Task created to run every 600 seconds
  2019-05-31 10:06:42,506 INFO [config.GeoserverXMLResourceProvider] - Found configuration file in /opt/data/gwc_cache_dir
  2019-05-31 10:06:42,516 INFO [config.GeoserverXMLResourceProvider] - Found configuration file in /opt/data/gwc_cache_dir
  2019-05-31 10:06:42,542 INFO [config.XMLConfiguration] - Wrote configuration to /opt/data/gwc_cache_dir
  2019-05-31 10:06:42,547 INFO [geoserver.importer] - Enabling import store: memory

Your ``GeoServer`` should be up and running at

.. code-block:: shell

  http://localhost:8080/geoserver/

.. warning:: In case of errors or the file ``geoserver.log`` is not created, check the Catalina logs in order to try to understand what's happened.

  .. code-block:: shell

    sudo less /usr/local/apache-tomcat8/logs/catalina.out

It is possible to test the new running ``GeoServer`` with the ``GeoNode`` paver service (``DEBUG`` mode). To do that

.. code-block:: shell

  workon geonode
  cd /opt/geonode/
  paver start_django

.. warning:: The ``paver reset`` command from now on **won't** clean up ``GeoServer`` and its catalog anymore. Therefore, every data uploaded during those tests will remain on ``GeoServer`` even if ``GeoNode`` will be reset.

Web Server
^^^^^^^^^^

Until now we have seen how to start ``GeoNode`` in ``DEBUG`` mode from the command line, through the ``paver`` utilities. This is of course not the best way to start it. Moreover you will need a dedicated ``HTTPD`` server running on port ``80`` if you would like to expose your server to the world.

In this section we will see:

1. How to configure ``NGINX`` HTTPD Server to host ``GeoNode`` and ``GeoServer``. In the initial setup we will still run the services on ``http://localhost``
2. Update the ``settings`` in order to link ``GeoNode`` and ``GeoServer`` to the ``PostgreSQL`` Database.
3. Update the ``settings`` in order to update ``GeoNode`` and ``GeoServer`` services running on a **public IP** or **hostname**.
4. Install and enable ``HTTPS`` secured connection through the ``Let's Encrypt`` provider.

Install and configure NGINX
...........................

.. warning:: Before executing the next steps, be sure ``GeoNode`` paver services have been stopped. To do that

  .. code-block:: shell

    workon geonode
    cd /opt/geonode/
    paver stop_django

.. code-block:: shell

  # Install the services
  sudo apt install -y nginx uwsgi uwsgi-plugin-python

Serving {“geonode”, “geoserver”} via NGINX
..........................................

.. code-block:: shell

  # Create the GeoNode UWSGI config
  sudo vim /etc/uwsgi/apps-available/geonode.ini

.. code-block:: shell

  [uwsgi]
  socket = 0.0.0.0:8000
  uid = geonode
  gid = www-data

  plugins = python
  virtualenv = /home/geonode/.virtualenvs/geonode
  env = DEBUG=False
  env = DJANGO_SETTINGS_MODULE=geonode.settings
  env = SECRET_KEY='RanD0m%3cr3tK3y'
  env = SITE_HOST_NAME=localhost
  env = SITEURL=http://localhost/
  env = LOCKDOWN_GEONODE=False
  env = SESSION_EXPIRED_CONTROL_ENABLED=True
  env = FORCE_SCRIPT_NAME=
  env = EMAIL_ENABLE=False
  env = DJANGO_EMAIL_HOST_USER=
  env = DJANGO_EMAIL_HOST_PASSWORD=
  env = DJANGO_EMAIL_HOST=localhost
  env = DJANGO_EMAIL_PORT=25
  env = DJANGO_EMAIL_USE_TLS=False
  env = DEFAULT_FROM_EMAIL=GeoNode <no-reply@localhost>
  env = MONITORING_ENABLED=True
  env = GEOSERVER_PUBLIC_HOST=localhost
  env = GEOSERVER_PUBLIC_PORT=
  env = GEOSERVER_ADMIN_PASSWORD=geoserver
  env = GEOSERVER_LOCATION=http://localhost/geoserver/
  env = GEOSERVER_PUBLIC_LOCATION=http://localhost/geoserver/
  env = GEOSERVER_WEB_UI_LOCATION=http://localhost/geoserver/
  env = RESOURCE_PUBLISHING=False
  env = ADMIN_MODERATE_UPLOADS=False
  env = GROUP_PRIVATE_RESOURCES=False
  env = GROUP_MANDATORY_RESOURCES=False
  env = OGC_REQUEST_TIMEOUT=60
  env = OGC_REQUEST_MAX_RETRIES=3
  env = OGC_REQUEST_POOL_MAXSIZE=100
  env = OGC_REQUEST_POOL_CONNECTIONS=100
  env = EXIF_ENABLED=True
  env = CREATE_LAYER=False
  env = FAVORITE_ENABLED=True

  chdir = /opt/geonode
  module = geonode.wsgi:application

  processes = 4
  threads = 2
  enable-threads = true
  master = true

  # logging
  # path to where uwsgi logs will be saved
  logto = /opt/data/logs/geonode.log
  daemonize = /opt/data/logs/geonode.log
  touch-reload = /opt/geonode/geonode/wsgi.py
  buffer-size = 32768
  max-requests = 500
  harakiri = 300 # respawn processes taking more than 5 minutes (300 seconds)
  max-requests = 500 # respawn processes after serving 5000 requests
  # limit-as = 1024 # avoid Errno 12 cannot allocate memory
  harakiri-verbose = true
  vacuum = true
  thunder-lock = true

.. code-block:: shell

  # Enable the GeoNode UWSGI config
  sudo ln -s /etc/uwsgi/apps-available/geonode.ini /etc/uwsgi/apps-enabled/geonode.ini

  # Restart UWSGI Service
  sudo service uwsgi restart

.. code-block:: shell

  # Backup the original NGINX config
  sudo mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.orig

  # Create the GeoNode Default NGINX config
  sudo vim /etc/nginx/nginx.conf

.. code-block:: shell

  # Make sure your nginx.config matches the following one
  user www-data;
  worker_processes auto;
  pid /run/nginx.pid;
  include /etc/nginx/modules-enabled/*.conf;

  events {
    worker_connections 768;
    # multi_accept on;
  }

  http {
    ##
    # Basic Settings
    ##

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    # server_tokens off;

    # server_names_hash_bucket_size 64;
    # server_name_in_redirect off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ##
    # SSL Settings
    ##

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
    ssl_prefer_server_ciphers on;

    ##
    # Logging Settings
    ##

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    ##
    # Gzip Settings
    ##

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_http_version 1.1;
    gzip_disable "MSIE [1-6]\.";
    gzip_buffers 16 8k;
    gzip_min_length 1100;
    gzip_comp_level 6;
    gzip_proxied any;
    gzip_types video/mp4 text/plain text/css application/x-javascript text/xml application/xml application/xml+rss text/javascript image/jpeg;

    ##
    # Virtual Host Configs
    ##

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
  }

.. code-block:: shell

  # Remove the Default NGINX config
  sudo rm /etc/nginx/sites-enabled/default

  # Create the GeoNode App NGINX config
  sudo vim /etc/nginx/sites-available/geonode

.. code-block:: shell

  uwsgi_intercept_errors on;

  upstream geoserver_proxy {
    server localhost:8080;
  }

  # Expires map
  map $sent_http_content_type $expires {
    default                    off;
    text/html                  epoch;
    text/css                   max;
    application/javascript     max;
    ~image/                    max;
  }

  server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;

    server_name _;

    charset utf-8;

    etag on;
    expires $expires;
    proxy_read_timeout 600s;
    # set client body size to 2M #
    client_max_body_size 50000M;

    location / {
      etag off;
      uwsgi_pass 127.0.0.1:8000;
      uwsgi_read_timeout 600s;
      include uwsgi_params;
    }

    location /static/ {
      alias /opt/geonode/geonode/static_root/;
    }

    location /uploaded/ {
      alias /opt/geonode/geonode/uploaded/;
    }

    location /geoserver {
      proxy_pass http://geoserver_proxy;
      include proxy_params;
    }
  }

.. code-block:: shell

  # Enable GeoNode NGINX config
  sudo ln -s /etc/nginx/sites-available/geonode /etc/nginx/sites-enabled/geonode

  # Restart the services
  sudo systemctl restart tomcat
  sudo service nginx restart

Refresh ``GeoNode`` static data

.. code-block:: shell

  workon geonode
  cd /opt/geonode
  python manage.py collectstatic --no-input


Refresh ``GeoNode`` and ``GeoServer`` **OAuth2** settings

.. code-block:: shell

  workon geonode
  cd /opt/geonode

  # This must be done the first time only
  sudo cp package/support/geonode.binary /usr/bin/geonode
  sudo cp package/support/geonode.updateip /usr/bin/geonode_updateip
  sudo chmod +x /usr/bin/geonode
  sudo chmod +x /usr/bin/geonode_updateip
  pip install -e git+https://github.com/justquick/django-activity-stream.git#egg=django-activity-stream

  # Update the GeoNode ip or hostname
  sudo PYTHONWARNINGS=ignore VIRTUAL_ENV=$VIRTUAL_ENV DJANGO_SETTINGS_MODULE=geonode.settings GEONODE_ETC=/opt/geonode GEOSERVER_DATA_DIR=/opt/data/geoserver_data TOMCAT_SERVICE="service tomcat" APACHE_SERVICE="service nginx" geonode_updateip -p localhost

The ``GeoNode`` service should now run on ``http://localhost/``

The ``GeoServer`` service should now run on ``http://localhost/geoserver/``

You should be able to login with the default user ``admin`` (pwd ``admin``) and upload your layers.

Update the settings in order to use the ``PostgreSQL`` Database
...............................................................

.. warning:: Make sure you already installed and configured the Database as explained in the previous sections.

.. code-block:: shell

  workon geonode
  cd /opt/geonode

  cp geonode/local_settings.py.geoserver.sample geonode/local_settings.py

  # In case you want to change the DB password, run the following
  # sudo sed -i -e "s/'PASSWORD': 'geonode',/'PASSWORD': '<your_db_role_password>',/g" geonode/local_settings.py

  # Stop Tomcat
  sudo systemctl stop tomcat

  # Initialize GeoNode
  DJANGO_SETTINGS_MODULE=geonode.local_settings paver reset
  DJANGO_SETTINGS_MODULE=geonode.local_settings paver setup
  DJANGO_SETTINGS_MODULE=geonode.local_settings paver sync
  DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py collectstatic --noinput

Before finalizing the configuration we will need to update the ``UWSGI`` settings

.. code-block:: shell

  sudo vim /etc/uwsgi/apps-enabled/geonode.ini

Change ``geonode.settings`` to ``geonode.local_settings``

.. code-block:: shell

  :%s/geonode.settings/geonode.local_settings/g
  :wq

Restart ``UWSGI`` and update ``OAuth2`` by using the new ``geonode.local_settings``

.. warning:: **!IMPORTANT!** In the statement below make sure to use ``DJANGO_SETTINGS_MODULE=geonode.local_settings``

.. code-block:: shell

  # Restart UWSGI
  sudo service uwsgi restart

  # Update the GeoNode ip or hostname
  sudo PYTHONWARNINGS=ignore VIRTUAL_ENV=$VIRTUAL_ENV DJANGO_SETTINGS_MODULE=geonode.local_settings GEONODE_ETC=/opt/geonode GEOSERVER_DATA_DIR=/opt/data/geoserver_data TOMCAT_SERVICE="service tomcat" APACHE_SERVICE="service nginx" geonode_updateip -p localhost

Update the settings in order to update GeoNode and GeoServer services running on a public IP or hostname
........................................................................................................

.. warning:: Before exposing your services to the Internet, **make sure** your system is **hardened** and **secure enough**. See the specific documentation section for more details.

Let's say you want to run your services on a public IP or domain, e.g. ``www.example.org``. You will need to slightly update your services in order to reflect the new server name.

In particular the steps to do are:

1. Update ``NGINX`` configuration in order to serve the new domain name.

  .. code-block:: shell

    sudo vim /etc/nginx/sites-enabled/geonode

    # Update the 'server_name' directive
    server_name example.org www.example.org;

    # Restart the service
    sudo service nginx restart

2. Update ``UWSGI`` configuration in order to serve the new domain name.

  .. code-block:: shell

    sudo vim /etc/uwsgi/apps-enabled/geonode.ini

    # Change everywhere 'localhost' to the new hostname
    %s/localhost/www.example.org/g

    # Restart the service
    sudo service uwsgi restart

3. Update ``OAuth2`` configuration in order to hit the new hostname.

  .. code-block:: shell

    workon geonode
    cd /opt/geonode

    # Update the GeoNode ip or hostname
    sudo PYTHONWARNINGS=ignore VIRTUAL_ENV=$VIRTUAL_ENV DJANGO_SETTINGS_MODULE=geonode.local_settings GEONODE_ETC=/opt/geonode GEOSERVER_DATA_DIR=/opt/data/geoserver_data TOMCAT_SERVICE="service tomcat" APACHE_SERVICE="service nginx" geonode_updateip -l localhost -p www.example.org

4. Update the existing ``GeoNode`` links in order to hit the new hostname.

  .. code-block:: shell

    workon geonode
    cd /opt/geonode

    # Update the GeoNode ip or hostname
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py migrate_baseurl --source-address=http://localhost --target-address=http://www.example.org

Install and enable HTTPS secured connection through the Let's Encrypt provider
..............................................................................

.. code-block:: shell

  # Install Let's Encrypt Certbot
  sudo add-apt-repository ppa:certbot/certbot
  sudo apt update -y; sudo apt install python-certbot-nginx -y

  # Reload NGINX config and make sure the firewall denies access to HTTP
  sudo systemctl reload nginx
  sudo ufw allow 'Nginx Full'
  sudo ufw delete allow 'Nginx HTTP'

  # Create and dump the Let's Encrypt Certificates
  sudo certbot --nginx -d example.org -d www.example.org
  # ...choose the redirect option when asked for

1. Update the ``GeoNode`` **OAuth2** ``Redirect URIs`` accordingly.

  From the ``GeoNode Admin Dashboard`` go to ``Home › Django/GeoNode OAuth Toolkit › Applications › GeoServer``

  .. figure:: img/ubuntu-https-001.png
        :align: center

        *Redirect URIs*

2. Update the ``GeoServer`` ``Proxy Base URL`` accordingly.

  From the ``GeoServer Admin GUI`` go to ``About & Status > Global``

  .. figure:: img/ubuntu-https-002.png
        :align: center

        *Proxy Base URL*


3. Update the ``GeoServer`` ``Role Base URL`` accordingly.

  From the ``GeoServer Admin GUI`` go to ``Security > Users, Groups, Roles > geonode REST role service``

  .. figure:: img/ubuntu-https-003.png
        :align: center

        *Role Base URL*

4. Update the ``GeoServer`` ``OAuth2 Service Parameters`` accordingly.

  From the ``GeoServer Admin GUI`` go to ``Security > Authentication > Authentication Filters > geonode-oauth2``

  .. figure:: img/ubuntu-https-004.png
        :align: center

        *OAuth2 Service Parameters*


5. Update the ``UWSGI`` configuration

  .. code-block:: shell

    sudo vim /etc/uwsgi/apps-enabled/geonode.ini

    # Change everywhere 'http' to 'https'
    %s/http/https/g

    # Add two more 'env' variables to the configuration
    env = SECURE_SSL_REDIRECT=True
    env = SECURE_HSTS_INCLUDE_SUBDOMAINS=True

    # Restart the service
    sudo service uwsgi restart

  .. figure:: img/ubuntu-https-005.png
        :align: center

        *UWSGI Configuration*

CentOS 7.0
==========

* TODO

Docker
======

In this section we are going to list the passages needed to:

1. Install ``Docker`` and ``docker-compose`` packages on a Ubuntu host
2. Deploy a vanilla ``GeoNode 2.10`` with ``Docker``

  a. Override the ``ENV`` variables to deploy on a ``public IP`` or ``domain``
  b. Access the ``django4geonode`` Docker image to update the code-base and/or change internal settings
  c. Access the ``geoserver4geonode`` Docker image to update the GeoServer version

3. Passages to completely get rid of old ``Docker`` images and volumes (prune the environment completely)

.. include:: docker/ubuntu.rst

.. include:: docker/centos.rst

Test Docker Compose Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Logout and login again on shell and then execute:

.. code-block:: shell

  docker run -it hello-world

Deploy a vanilla GeoNode 2.10 with Docker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Clone the Project

.. code-block:: shell

  # Let's create the GeoNode core base folder and clone it
  sudo mkdir -p /opt/geonode/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode/
  sudo chmod -Rf 775 /opt/geonode/

  # Clone the GeoNode source code on /opt/geonode
  cd /opt
  git clone https://github.com/GeoNode/geonode.git geonode

Start the Docker instances on ``localhost``

.. warning:: The first time pulling the images will take some time. You will need a good internet connection.

.. code-block:: shell

  cd /opt/geonode
  docker-compose -f docker-compose.yml -f docker-compose.override.localhost.yml pull
  docker-compose -f docker-compose.yml -f docker-compose.override.localhost.yml up -d

.. note:: If you want to re-build the docker images from scratch, instead of ``pulling`` them from the ``Docker Hub`` add the ``--build`` parameter to the up command, for instance:

  .. code-block:: shell

    docker-compose -f docker-compose.yml -f docker-compose.override.localhost.yml up --build

  In this case you can of course skip the ``pull`` step to download the ``pre-built`` images.

.. note:: To startup the containers daemonized, which means they will be started in the background (and keep running if you ``log out`` from the server or close the ``shell``) add the ``-d`` option to the ``up`` command as in the following. ``docker-compose`` will take care to restart the containers if necessary (e.g. after boot).

  .. code-block:: shell

    docker-compose -f docker-compose.yml -f docker-compose.override.localhost.yml up -d

    # If you want to rebuild the images also
    docker-compose -f docker-compose.yml -f docker-compose.override.localhost.yml up --build -d

Test the instance and follow the logs
.....................................

If you run the containers daemonized (with the ``-d`` option), you can either run specific Docker commands to follow the ``startup and initialization logs`` or entering the image ``shell`` and check for the ``GeoNode logs``.

In order to follow the ``startup and initialization logs``, you will need to run the following command from the repository folder

.. code-block:: shell

  cd /opt/geonode
  docker logs -f django4geonode

Alternatively:

.. code-block:: shell

  cd /opt/geonode
  docker-compose logs -f django

You should be able to see several initialization messages. Once the container is up and running, you will see the following statements

.. code-block:: shell

  ...
  789 static files copied to '/mnt/volumes/statics/static'.
  static data refreshed
  Executing UWSGI server uwsgi --ini /usr/src/app/uwsgi.ini for Production
  [uWSGI] getting INI configuration from /usr/src/app/uwsgi.ini

To exit just hit ``CTRL+C``.

This message means that the GeoNode containers have bee started. Browsing to ``http://localhost/`` will show the GeoNode home page. You should be able to successfully log with the default admin user (``admin`` / ``admin``) and start using it right away.

With Docker it is also possible to run a shell in the container and follow the logs exactly the same as you deployed it on a physical host. To achieve this run

.. code-block:: shell

  docker exec -it django4geonode /bin/bash

  # Once logged in the GeoNode image, follow the logs by executing
  tail -F -n 300 /var/log/geonode.log

Alternatively:

.. code-block:: shell

  docker-compose exec django /bin/bash

To exit just hit ``CTRL+C`` and ``exit`` to return to the host.

Override the ENV variables to deploy on a public IP or domain
.............................................................

If you would like to start the containers on a ``public IP`` or ``domain``, let's say ``www.example.org``, you can

.. code-block:: shell

  cd /opt/geonode

  # Stop the Containers (if running)
  docker-compose stop

Edit the ``ENV`` override file in order to deploy on ``www.example.org``

.. code-block:: shell

  # Make a copy of docker-compose.override.localhost.yml
  cp docker-compose.override.localhost.yml docker-compose.override.example-org.yml

Replace everywhere ``localhost`` with ``www.example.org``

.. code-block:: shell

  vim docker-compose.override.example-org.yml

.. code-block:: shell

  # e.g.: :%s/localhost/www.example.org/g

  version: '2.2'
  services:

    django:
      build: .
      # Loading the app is defined here to allow for
      # autoreload on changes it is mounted on top of the
      # old copy that docker added when creating the image
      volumes:
        - '.:/usr/src/app'
      environment:
        - DEBUG=False
        - GEONODE_LB_HOST_IP=www.example.org
        - GEONODE_LB_PORT=80
        - SITEURL=http://www.example.org/
        - ALLOWED_HOSTS=['www.example.org', ]
        - GEOSERVER_PUBLIC_LOCATION=http://www.example.org/geoserver/
        - GEOSERVER_WEB_UI_LOCATION=http://www.example.org/geoserver/

    celery:
      build: .
      volumes:
        - '.:/usr/src/app'
      environment:
        - DEBUG=False
        - GEONODE_LB_HOST_IP=www.example.org
        - GEONODE_LB_PORT=80
        - SITEURL=http://www.example.org/
        - ALLOWED_HOSTS=['www.example.org', ]
        - GEOSERVER_PUBLIC_LOCATION=http://www.example.org/geoserver/
        - GEOSERVER_WEB_UI_LOCATION=http://www.example.org/geoserver/

    geoserver:
      environment:
        - GEONODE_LB_HOST_IP=www.example.org
        - GEONODE_LB_PORT=80
    #    - NGINX_BASE_URL=

.. note:: It is possible to override here even more variables to customize the GeoNode instance. See the ``GeoNode Settings`` section in order to get a list of the available options.

Run the containers in daemon mode

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.example-org.yml up --build -d

Access the django4geonode Docker container to update the code-base and/or change internal settings
..................................................................................................

Access the container ``bash``

.. code-block:: shell

  docker exec -i -t django4geonode /bin/bash

You will be logged into the GeoNode instance as ``root``. The folder is ``/usr/src/app/`` where the GeoNode project is cloned. Here you will find the GeoNode source code as in the GitHub repository.

.. note:: The machine is empty by default, no ``Ubuntu`` packages installed. If you need to install text editors or something you have to run the following commands:

  .. code-block:: shell

    apt update
    apt install <package name>

    e.g.:
      apt install vim

Update the templates or the ``Django models``. Once in the ``bash`` you can edit the templates or the Django models/classes. From here you can run any standard ``Django management command``.

Whenever you change a ``template/CSS/Javascript`` remember to run later:

.. code-block:: shell

  python manage.py collectstatic

in order to update the files into the ``statics`` Docker volume.

.. warning:: This is an external volume, and a simple restart won't update it. You have to be careful and keep it aligned with your changes.

Whenever you need to change some settings or environment variable, the easiest thing to do is to:

.. code-block:: shell

  # Stop the container
  docker-compose stop

  # Restart the container in Daemon mode
  docker-compose -f docker-compose.yml -f docker-compose.override.<whatever>.yml up -d

Whenever you change the model, remember to run later in the container via ``bash``:

.. code-block:: shell

  python manage.py makemigrations
  python manage.py migrate

Access the geoserver4geonode Docker container to update the GeoServer version
.............................................................................

This procedure allows you to access the GeoServer container.

The concept is exactly the same as above, log into the container with ``bash``.

.. code-block:: shell

  # Access the container bash
  docker exec -it geoserver4geonode /bin/bash

You will be logged into the GeoServer instance as ``root``.

GeoServer is deployed on an Apache Tomcat instance which can be found here

.. code-block:: shell

  cd /usr/local/tomcat/webapps/geoserver

.. warning:: The GeoServer ``DATA_DIR`` is deployed on an external Docker Volume ``geonode_gsdatadir``. This data dir won’t be affected by changes to the GeoServer application since it is ``external``.

Update the GeoServer instance inside the GeoServer Container

.. warning:: The old configuration will be kept since it is ``external``

.. code-block:: shell

	docker exec -it geoserver4geonode bash

.. code-block:: shell

  cd /usr/local/tomcat/
  wget --no-check-certificate https://build.geo-solutions.it/geonode/geoserver/latest/geoserver-2.14.3.war
  mkdir tmp/geoserver
  cd tmp/geoserver/
  unzip /usr/local/tomcat/geoserver-2.14.3.war
  rm -Rf data
  cp -Rf /usr/local/tomcat/webapps/geoserver/data/ .
  cd /usr/local/tomcat/
  mv webapps/geoserver/ .
  mv tmp/geoserver/ webapps/
  exit

.. code-block:: shell

  docker restart geoserver4geonode

.. warning::

  GeoNode 2.8.1 is **NOT** compatible with GeoServer > 2.13.x

  GeoNode 2.8.2 / 2.10.x are **NOT** compatible with GeoServer < 2.14.x

Remove all data and bring your running GeoNode deployment to the initial stage
..............................................................................

This procedure allows you to stop all the containers and reset all the data with the deletion of all the volumes.

.. code-block:: shell

  cd /opt/geonode

  # stop containers and remove volumes
  docker-compose down -v

Passages to completely get rid of old Docker images and volumes (reset the environment completely)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: For more details on Docker commands, please refer to the official Docker documentation.

It is possible to let docker show which containers are currently running (add ``-a`` for all containers, also stopped ones)

.. code-block:: shell

  # Show the currently running containers
  docker ps

  CONTAINER ID        IMAGE                      COMMAND                  CREATED             STATUS              PORTS                NAMES
  3b232931f820        geonode/nginx:production    "nginx -g 'daemon of…"   26 minutes ago      Up 26 minutes       0.0.0.0:80->80/tcp   nginx4geonode
  ff7002ae6e91        geonode/geonode:latest     "/usr/src/app/entryp…"   26 minutes ago      Up 26 minutes       8000/tcp             django4geonode
  2f155e5043be        geonode/geoserver:2.14.3   "/usr/local/tomcat/t…"   26 minutes ago      Up 26 minutes       8080/tcp             geoserver4geonode
  97f1668a01b1        geonode_celery             "/usr/src/app/entryp…"   26 minutes ago      Up 26 minutes       8000/tcp             geonode_celery_1
  1b623598b1bd        geonode/postgis:10         "docker-entrypoint.s…"   About an hour ago   Up 26 minutes       5432/tcp             db4geonode


Stop all the containers by running

.. code-block:: shell

  docker-compose stop

Force kill all containers by running

.. code-block:: shell

  docker kill $(docker ps -q)

I you want to clean up all containers and images, without deleting the static volumes (i.e. the ``DB`` and the ``GeoServer catalog``), issue the following commands

.. code-block:: shell

  # Remove all containers
  docker rm $(docker ps -a -q)

  # Remove all docker images
  docker rmi $(docker images -q)

  # Prune the old images
  docker system prune -a

If you want to remove a ``volume`` also

.. code-block:: shell

  # List of the running volumes
  docker volume ls

  # Remove the GeoServer catalog by its name
  docker volume rm -f geonode-gsdatadir

  # Remove all dangling docker volumes
  docker volume rm $(docker volume ls -qf dangling=true)

  # update all images, should be run regularly to fetch published updates
  for i in $(docker images| awk 'NR>1{print $1":"$2}'| grep -v '<none>'); do docker pull "$i" ;done
