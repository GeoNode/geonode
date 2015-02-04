.. _quick_installation:

========================
Quick Installation Guide
========================

The following is a quick guide to get GeoNode up and running in most common operating systems.
This is meant to be run on a fresh machine with no previously installated packages or GeoNode versions.

Recommended Minimum System Requirements
=======================================

For deployment of GeoNode on a single server, the following are the *bare minimum* system requirements:

* 6GB of RAM, including swap space.
* 2.2GHz processor. (Additional processing power may be required for multiple concurrent styling renderings)
* 1 GB software disk usage.
* Additional disk space for any data hosted with GeoNode and tiles cached with GeoWebCache.
  For spatial data, cached tiles, and "scratch space" useful for administration, a decent baseline size for GeoNode deployments is 100GB.
* 64-bit hardware recommended.


Linux
=====

Ubuntu
------

The easiest way to get the .deb is to install it using APT, the standard installation management tool for Ubuntu and other Debian-based systems.

0. First, make sure you have the ``add-apt-repository`` binary available.

   a) On Ubuntu 12.04 and older::

       sudo apt-get install python-software-properties

   b) On Ubuntu 12.10 and later::

       sudo apt-get install software-properties-common

1. Set up the GeoNode PPA repository (you only need to do this once; the repository will still be available for upgrades later)::

    sudo add-apt-repository ppa:geonode/release

2. Install the package.
   This step will also automatically download all necessary dependencies::

    sudo apt-get update
    sudo apt-get install geonode

3. Create a superuser and set the IP address
    a) $ geonode createsuperuser
    b) $ sudo geonode-updateip 127.0.0.1
    
4. Read the Admin Docs
    http://docs.geonode.org/en/master/#for-administrators


Windows, OSX and others
=======================


Windows
-------

To install in Windows it is assumed you're familiar with python development and virtualenv on Windows and that you're familiar with the windows command prompt. You will need the follow prerequists installed:

    * Java JDK
    * Python 2.7.9
      * Earlier versions of python require you to installdistutils (easy_install) - http://www.lfd.uci.edu/~gohlke/pythonlibs/#setuptools
    * ant (bin directory must be on system PATH)
    * maven2 (bin directory must be on system PATH)
    * git

Install and configure from the windows command prompt, if you don't already have python virtualenv installed, then do it now::
   
   easy_install virtualenv

Create virtualenv and activate it::
    
    cd <Directory to install the virtualenv & geonode into>
    virtualenv <name of virtualenv folder>
    virtualenv <name of virtualenv folder>\scripts\activate

Clone GeoNode::
    
    git clone https://github.com/GeoNode/geonode.git

    cd geonode

Install Python native dependencies, this command will look for and install binary distributions (pip install will attempt to build and fail)::
    
    pip install paver
    paver win_install_deps


    
Install GeoNode in the local virtualenv::

    pip install -e .

You have two options to set up the geos and gdal libraries.  Either create an environment variable
or add the variables to your local_settings.py file as below.

    GEOS_LIBRARY_PATH="C:/path/to/geos_c.dll"
    GDAL_LIBRARY_PATH="C:/path/to/gdal111.dll"

The geos and gdal libraries can be found in your <virtualenv directory>\Lib\site-packages\GDAL-1.11.0-py2.7-win32.egg\osgeo\ folder.

    
Setup GeoServer::
    
    paver setup
    
Start the servers.  You have the option to set the JAVA_HOME environment variable or use the --java_path.::

    paver start --java_path="C:\path\to\java\java.exe"

or if you set your JAVA_HOME environment variables (e.g. JAVA_HOME="C:\Program Files\Java\jdk1.7.0_75\")

    paver start

Once the package is installed, please consult :ref:`configure_installation` to learn how to create an account for the admin user and tweak the settings to get more performance.

OSX
---

The recommended install method in these platforms is to use a virtualization solution, like `Virtual Box`_, install the latest `Ubuntu Linux`_ and then proceed with the steps mentioned above. Some GeoNode developers prefer to use `Vagrant`_ - a VirtualBox wrapper, the steps for this are detailed below. The Vagrant quickstart guide shows how to get a Linux VM configured in most operating systems. However, if you would like to develop natively on OSX please follow the following instructions.

You may need brew install various dependencies::

    mkdir -p ~/pyenv
    virtualenv ~/pyenv/geonode    
    source ~/pyenv/geonode/bin/activate
    git clone https://github.com/GeoNode/geonode
    cd geonode
    pip install lxml
    pip install pyproj
    pip install nose
    pip install httplib2
    pip install shapely
    pip install pillow
    pip install paver

Node and tools required for static development::

    brew install node
    npm install -g bower
    npm install -g grunt-cli

Install pip dependencies::

    pip install -e .

Paver handles dependencies for Geonode, first setup (this will download and update your python dependencies - ensure you're in a virtualenv)::

    paver setup
    paver start
    
Optional: To generate document thumbnails for PDFs and other ghostscripts file types, download ghostscript: https://www.macupdate.com/app/mac/9980/gpl-ghostscript::

    sudo apt-get install imagemagick
    brew install imagemagick
    pip install Wand==0.3.5

Once fully started, you should see a message indicating the address of your geonode.
The default username and password are ``admin`` and ``admin``::
  
  Development GeoNode is running at http://localhost:8000/
  The GeoNode is an unstoppable machine
  Press CTRL-C to shut down

Before starting GeoNode (paver start), you could test your installation by running tests::

    paver test
    paver test_integration
    
In case you want to build yourself the documentation, you need to install Sphinx and the run 'make html' from within the docs directory::

    pip install Sphinx
    cd docs
    make html
    
You can eventually generate a pdf containing the whole documentation set. For this purpose, if using Ubuntu 12.4 you will need to install the texlive-full package::

    sudo apt-get install texlive-full
    make latexpdf

.. note:: 

  When running ``virtualenv venv`` the ``--system-site-packages`` option is
  not required.  If not enabled, the bootstrap script will sandbox your virtual
  environment from any packages that are installed in the system, useful if
  you have incompatible versions of libraries such as Django installed
  system-wide.  On the other hand, most of the times it is useful to use a version of
  the Python Imaging Library provided by your operating system
  vendor, or packaged other than on PyPI.  When in doubt, however, just leave
  this option out.


  Vagrant
  -------

http://docs.vagrantup.com/v2/getting-started/index.html

.. _Virtual Box: http://virtualbox.org
.. _Vagrant: http://vagrantup.com
.. _Ubuntu Linux: http://www.ubuntu.com/download



CentOS/RHEL and other \*nix distros
-----------------------------------

We recommend you to download the latest release and modify the included ``install.sh`` and ``support/config.sh``. GeoNode has been installed in CentOS/RHEL using this mechanism.

Once the package is installed, please consult the :ref:`configure_installation` to learn how to create the admin user and tweak the settings to get more performance.

