Overview
========

The following steps will guide you to a new setup of GeoNode Project. All guides will first install and configure the system to run it in ``DEBUG`` mode (also known as ``DEVELOPMENT`` mode) and then by configuring an HTTPD server to serve GeoNode through the standard ``HTTP`` (``80``) port.

Those guides **are not** meant to be used on a production system. There will be dedicated chapters that will show you some *hints* to optimize GeoNode for a production-ready machine. In any case, we strongly suggest to task an experienced *DevOp* or *System Administrator* before exposing your server to the ``WEB``.

.. contents::
   :depth: 4

Ubuntu 18.04
============

This part of the documentation describes the complete setup process for GeoNode on an Ubuntu 18.04 64-bit clean environment (Desktop or Server). All examples use shell commands that you must enter on a local terminal or a remote shell.
- If you have a graphical desktop environment you can open the terminal application after login;
- if you are working on a remote server the provider or sysadmin should has given you access through an ssh client.

.. _install_dep_proj:

Install the dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

In this section, we are going to install all the basic packages and tools needed for a complete GeoNode installation. To follow this guide, a piece of basic knowledge about Ubuntu Server configuration and working with a shell is required. This guide uses ``vim`` as the editor; fill free to use ``nano``, ``gedit`` or others.

Upgrade system packages
.......................

Check that your system is already up-to-date with the repository running the following commands:

.. code-block:: shell

   sudo apt update
   sudo apt upgrade


Create a Dedicated User
.......................

In the following steps a User named ``geonode`` is used: to run installation commands the user must be in the ``sudo`` group.

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

Packages Installation
.....................

First, we are going to install all the **system packages** needed for the GeoNode setup.

.. code-block:: shell

  # Install packages from GeoNode core
  sudo apt install -y python-gdal gdal-bin
  sudo apt install -y python-pip python-dev python-virtualenv
  sudo apt install -y libxml2 libxml2-dev gettext
  sudo apt install -y libxslt1-dev libjpeg-dev libpng-dev libpq-dev libgdal-dev libgdal20
  sudo apt install -y software-properties-common build-essential
  sudo apt install -y git unzip gcc zlib1g-dev libgeos-dev libproj-dev
  sudo apt install -y sqlite3 spatialite-bin libsqlite3-mod-spatialite

  # Install Openjdk
  sudo -i apt update
  sudo apt install openjdk-8-jdk-headless default-jdk-headless -y
  sudo update-java-alternatives --jre-headless --jre --set java-1.8.0-openjdk-amd64

  sudo apt update -y
  sudo apt upgrade -y
  sudo apt autoremove -y
  sudo apt autoclean -y
  sudo apt purge -y
  sudo apt clean -y

  # Install Packages for Virtual environment management
  sudo apt install -y virtualenv virtualenvwrapper

Geonode Project Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Geonode project is the proper way to run a customized installation of Geonode. The repository of geonode-project contains a minimal set of files following the structure of a django-project. Geonode itself will be installed as a requirement of your project.
Inside the project structure is possible to extend, replace or modify all geonode componentse (e.g. css and other static files, templates, models..) and even register new django apps **without touching the original Geonode code**.


.. note:: You can call your geonode project whatever you like following the naming conventions for python packages (generally lower case with underscores (_). In the examples below, replace ``my_geonode`` with whatever you would like to name your project.

See also the `README <https://github.com/GeoNode/geonode-project/blob/master/README.rst>`_ fiel on geonode-project repository

First of all we need to prepare a new Python Virtual Environment

Check that the file ``virtualenvwrapper.sh`` exists in the ``$HOME/.local/bin/`` (``$HOME`` is the current user home directory and in our case should be ``/home/geonode``) and then add this line to your file ``~/.bashrc``

.. code-block:: shell

  vim ~/.bashrc

.. code-block:: shell

  # virtualenv
  source $HOME/.local/bin/virtualenvwrapper.sh

Then run the ``.bashrc`` from shell

.. code-block:: shell

  source ~/.bashrc
  #create a new virtualenv called geonode
  mkvirtualenv --no-site-packages geonode

At this point, your command prompt shows a ``(geonode)`` prefix, this indicates that your virtualenv is active.

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
  GDAL_VERSION=`gdal-config --version`; \
    PYGDAL_VERSION="$(pip install pygdal==$GDAL_VERSION 2>&1 | grep -oP '(?<=: )(.*)(?=\))' | grep -oh $GDAL_VERSION\.[0-9])"; \
    pip install pygdal==$PYGDAL_VERSION




TODO

Docker
======

.. warning:: Before moving with this section, you should have read and clearly understood the ``INSTALLATION > GeoNode Core`` sections, and in particular the ``Docker`` one. Everything said for the GeoNode Core Vanilla applies here too, except that the Docker container names will be slightly different. As an instance if you named your project ``my_geonode``, your containers will be called:

  .. code-block:: shell

    'django4my_geonode' instead of 'django4geonode' and so on...

Deploy an instance of a geonode-project Django template 2.10.x with Docker on localhost
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prepare the environment

.. code-block:: shell

  sudo mkdir -p /opt/geonode_custom/
  sudo usermod -a -G www-data geonode
  sudo chown -Rf geonode:www-data /opt/geonode_custom/
  sudo chmod -Rf 775 /opt/geonode_custom/

Clone the source code

.. code-block:: shell

  cd /opt/geonode_custom/
  git clone https://github.com/GeoNode/geonode-project.git

Make an instance out of the ``Django Template``

.. note:: We will call our instance ``my_geonode``. You can change the name at your convenience.

.. code-block:: shell

  mkvirtualenv my_geonode
  pip install Django==1.11.21
  django-admin startproject --template=./geonode-project -e py,rst,json,yml,ini,env,sample -n Dockerfile my_geonode
  cd /opt/geonode_custom/my_geonode

Modify the code and the templates and rebuild the Docker Containers

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.yml build --no-cache

Finally, run the containers

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

Deploy an instance of a geonode-project Django template 2.10.x with Docker on a domain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: We will use ``www.example.org`` as an example. You can change the name at your convenience.

Stop the containers

.. code-block:: shell

  cd /opt/geonode_custom/my_geonode

  docker-compose -f docker-compose.yml -f docker-compose.override.yml stop

Edit the ``ENV`` override file in order to deploy on ``www.example.org``

.. code-block:: shell

  # Make a copy of docker-compose.override.yml
  cp docker-compose.override.yml docker-compose.override.example-org.yml

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
        - '.:/usr/src/my_geonode'
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
        - GEONODE_LB_HOST_IP=localhost
        - GEONODE_LB_PORT=80
    #    - NGINX_BASE_URL=


.. note:: It is possible to override here even more variables to customize the GeoNode instance. See the ``GeoNode Settings`` section in order to get a list of the available options.

Run the containers in daemon mode

.. code-block:: shell

  docker-compose -f docker-compose.yml -f docker-compose.override.example-org.yml up --build -d
