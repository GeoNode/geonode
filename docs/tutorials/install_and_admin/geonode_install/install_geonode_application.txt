.. _install_geonode_application:

===========================
Install GeoNode Application
===========================

In this section you are going to install all the basic packages and tools needed
for a complete GeoNode installation.

Login
=====

When you first start the Virtual Machine at the end of the boot process
you will be prompted for the user password to login. Enter `geo` as user
password and press `Enter`.

.. image:: img/login.png
   :width: 600px
   :alt: User Login

You are now logged in as user 'geo'. On the left side of the screen there
is a panel with shortcuts to common applications, launch a the terminal
emulator.

.. image:: img/open_terminal.png
   :width: 600px
   :alt: Launch terminal emulator

Packages Installation
=====================

First we are going to install all the software packages we are going to need
for the GeoNode setup. Among others `Tomcat 8`, `PostgreSQL`, `PostGIS`,
`Apache HTTP server` and `Git`. Run the following command to install all the
packages

.. code-block:: bash

    $ sudo apt-get update
        
    $ sudo apt-get install python-virtualenv python-dev libxml2 libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libpq-dev libgdal-dev git default-jdk
    $ sudo apt-get install build-essential openssh-server gettext nano vim unzip zip patch git-core postfix

    $ sudo apt-add-repository ppa:webupd8team/java
    $ sudo apt-get update
    $ sudo apt-get install oracle-java8-installer

    $ sudo apt-add-repository ppa:ubuntugis && sudo apt-get update && sudo apt-get upgrade
    $ sudo apt-add-repository ppa:ubuntugis/ppa && sudo apt-get update && sudo apt-get upgrade
    $ sudo apt-get install gcc apache2 libapache2-mod-wsgi libgeos-dev libjpeg-dev libpng-dev libpq-dev libproj-dev libxml2-dev libxslt-dev
    $ sudo apt-add-repository ppa:ubuntugis/ubuntugis-testing && sudo apt-get update && sudo apt-get upgrade
    $ sudo apt-get install gdal-bin libgdal20 libgdal-dev
    $ sudo apt-get install python-gdal python-pycurl python-imaging python-pastescript python-psycopg2 python-urlgrabber  
    $ sudo apt-get install postgresql postgis postgresql-9.5-postgis-scripts postgresql-contrib
    $ sudo apt-get install tomcat8

    $ sudo apt-get update && sudo apt-get upgrade && sudo apt-get autoremove && sudo apt-get autoclean && sudo apt-get purge && sudo apt-get clean

.. image:: img/install_packages.png
   :width: 600px
   :alt: Install Packages

.. note:: If you will be prompted for `geo` user's password (`geo`) and for confirmation twice

    .. image:: img/confirm_Install.png
       :width: 600px
       :alt: Confirm Installation

.. warning:: The installation process is going to take several minutes and it will need to download packages from Internet.

At this point we have all the packages we need on the system.

GeoNode Setup
=============
First of all we need to prepare a new Python Virtual Environment:

.. code-block:: bash

    $ sudo apt install python-pip
    $ pip install --upgrade pip
    $ pip install --user virtualenv
    $ pip install --user virtualenvwrapper
    # The commands above will install the Python Venv packages

    $ export WORKON_HOME=~/Envs
    $ mkdir -p $WORKON_HOME
    $ source $HOME/.local/bin/virtualenvwrapper.sh
    $ printf '\n%s\n%s\n%s' '# virtualenv' 'export WORKON_HOME=~/Envs' 'source $HOME/.local/bin/virtualenvwrapper.sh' >> ~/.bashrc
    $ source ~/.bashrc
    # We have now configured the user environment

    $ mkvirtualenv --no-site-packages geonode
    # Through this command we have created a brand new geonode Virual Environment

    $ sudo useradd -m geonode
    $ sudo usermod -a -G geonode geo
    $ sudo chmod -Rf 775 /home/geonode/
    $ sudo su - geo
    # The commands above are needed only if geo and geonode users have not been already defined

Let's activate the new `geonode` Python Virtual Environment:

.. code-block:: bash
    
    $ workon geonode

Move into the `geonode` home folder

.. code-block:: bash

    $ cd /home/geonode

We are going to install GeoNode as a dependency of a **Customized DJango Project**

.. note::
    A custom project is a DJango application with *ad hoc* configuration and folders, which allows you to 
    extend the original **GeoNode** code without actually dealing or modifying the main source code.
    
    This will allow you to easily customize your GeoNode instance, modify the theme, add new functionalities and so on,
    and also being able to keep updated with the GeoNode latest source code.
    
    For more deails please check https://github.com/GeoNode/geonode-project/tree/master

.. code-block:: bash

    $ pip install Django==1.8.18
    $ django-admin.py startproject --template=https://github.com/GeoNode/geonode-project/archive/2.9.x-rev.zip -e py,rst,json,yml my_geonode

Let's install the GeoNode dependencies and packages into the Python Virtual Environment:

.. code-block:: bash

    $ cd my_geonode
    $ vim requirements.txt
    # Make sure requirements contains reference to geonode master branch
    -e git://github.com/GeoNode/geonode.git@master#egg=geonode

    $ pip install -r requirements.txt
    $ pip install -e .
    $ pip install pygdal==2.2.1.3
    # The closest to your `gdal-config --version`

In the next section we are going to setup PostgreSQL Databases for GeoNode and finalize the setup
