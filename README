.. image:: https://coveralls.io/repos/github/GeoNode/geonode/badge.svg?branch=master
    :alt: Coverage Badge
    :target: https://coveralls.io/github/GeoNode/geonode?branch=master

.. image:: https://secure.travis-ci.org/GeoNode/geonode.png
    :alt: Build Status
    :target: http://travis-ci.org/GeoNode/geonode


GeoNode Support 
===============

To get support, give feedback and suggestions please use the GeoNode official channels, the users mailing list: http://lists.osgeo.org/pipermail/geonode-users/ and the developers mailing list: http://lists.osgeo.org/pipermail/geonode-devel/.

This repository is used to track code changes and GeoNode issues, please DON'T open new issues to ask for support.


GeoNode Installation
====================

If you just want to try GeoNode, it is recommended to use Ubuntu 14.04 and install the latest stable release of GeoNode.::

    sudo add-apt-repository ppa:geonode/release
    sudo apt-get update
    sudo apt-get install geonode

If instead, you are interested in doing development on the source code, here are the instructions: http://docs.geonode.org/en/master/tutorials/devel/devel_env/index.html

Development Installations
=========================

Docker Usage
------------

If you want to use Docker you can now::

    # build the docker container
    docker-compose build

    # run the docker container
    docker-compose up

    # turn it off
    docker-compose down

Or if you want to use the provided Makefile::

    # build the container
    make build

    # run the container
    make up

    # create database
    make sync

    # pull latest images
    make pull



Ubuntu
------

Ubuntu development build instructions using an isolated virtual environment (tested on Ubuntu 14.04 LTS)::

    # Install Ubuntu dependencies
    sudo apt-get update
    sudo apt-get install python-virtualenv python-dev libxml2 libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libpq-dev libgdal-dev git default-jdk

    # Install Java 8 (needed by latest GeoServer 2.9)
    sudo apt-add-repository ppa:webupd8team/java
    sudo apt-get update
    sudo apt-get install oracle-java8-installer

    # Create and activate the virtulenv
    virtualenv --no-site-packages env
    source env/bin/activate

    # git clone geonode
    git clone https://github.com/GeoNode/geonode
    cd geonode

    # Install pip dependencies
    pip install -r requirements.txt
    pip install -e .
    pip install pygdal==1.10.1

You can now setup and start GeoNode::

    # Paver setup
    paver setup
    paver sync
    paver start

In case you want to be involved in static files development::

    sudo apt-get install npm
    sudo npm install -g bower
    sudo npm install -g grunt-cli


openSUSE
--------

openSUSE Development Build Instructions::

    # Add Application:Geo and Python repositories
    zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_12.2/ GEO
    zypper -ar http://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_12.1/ python
    zypper refresh

    # Basic build packages
    zypper install gcc gcc-c++ python-devel libgeos-devel libproj-devel

    # Python native dependencies
    zypper install python-pip python-virtualenv python-imaging python-lxml python-gdal

    # Java dependencies
    zypper install java-1_7_0_openjdk-devel ant maven

    # Supporting tools
    zypper install git gettext-runtime

    # Create virtualenv and activate it
    virtualenv venv --system-site-packages
    source venv/bin/activate
    cd venv

    # Clone GeoNode
    git clone https://github.com/GeoNode/geonode.git

    # Install GeoNode in the local virtualenv
    pip install -e geonode --use-mirrors

    cd geonode

    # Compile GeoServer
    paver setup

    # Initialize database
    paver sync

    # Start the servers
    paver start

Windows
-------

Windows Development Build Instructions::


    Prerequisites:
    # Java JDK
    # Python 2.7 (32 bit)
    # ant (bin directory must be on system PATH)
    # maven2 (bin directory must be on system PATH)
    # Python distutils (easy_install)
    # GDAL Core Libraries
    # git

    # Install and configure from the windows command prompt
    If you don't already have python virtualenv installed, then do it now:
    easy_install virtualenv

    # Download and install http://download.gisinternals.com/sdk/downloads/release-1800-gdal-1-11-4-mapserver-6-4-3/gdal-111-1800-core.msi
    # Download and install http://download.gisinternals.com/sdk/downloads/release-1800-gdal-1-11-4-mapserver-6-4-3/GDAL-1.11.4.win32-py2.7.msi
    # Choose your 32 bit python as your install target
    # If you create your virtualenv before doing this, you can copy the <python>\lib\site-packages\osgeo and GDAL-* directory over to your <virtual env>\lib\site-packages directory

    # Create virtualenv and activate it
    cd <Directory to install the virtualenv & geonode into>
    virtualenv venv
    venv\scripts\activate

    # Clone GeoNode
    git clone https://github.com/GeoNode/geonode.git

    # Install compiled packages for Python 2.7 Win32
    cd geonode
    pip install paver
    pip install pyyaml
    paver win_install_deps

    # Install GeoNode in the local virtualenv, if you get an error about use-mirrors, just remove the argument
    pip install -e . --use-mirrors

    # Note, you may get errors due to certain dependencies not being installable on windows with pip, such as lxml and shapely.
    # For these, you can download a whl file (use cp27 / win32 version) from http://www.lfd.uci.edu/~gohlke/pythonlibs and then install them via pip.
    # Ex: pip install <Download Dir>\Shapely-1.5-16-cp27-cp27m-win32.whl
    #
    # Also note, you may have to adjust the dependencies in geonode\setup.py to say >= instead of ==,
    # ie "Shapely>=1.5.13", instead of "Shapely==1.5.13",

    # Compile GeoServer
    paver setup

    # Set GDAL environment info
    SET GDAL_LIBRARY_PATH=<GdalPath>\gdal111.dll
    SET GDAL_HOME=<GdalPath>
    SET GEOS_LIBRARY_PATH=<GdalPath>\geos_c.dll
    SET PATH=<GdalPath>;%PATH%

    # Initialize database
    paver sync

    # Start the servers
    paver start --java_path=C:/path/to/java/bin/java.exe



Mac OSX
-------

Mac OSX Development Build Instructions::

    # you may need brew install various dependencies

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

    # Node and tools required for static development
    brew install node
    npm install -g bower
    npm install -g grunt-cli

    #Install pip dependencies
    pip install -e .

    #Paver handles dependencies for Geonode, first setup (this will download and update your python dependencies - ensure you're in a virtualenv)
    paver setup
    paver sync
    paver start

    # Optional: To generate document thumbnails for PDFs and other ghostscripts file types
    # Then download ghostscript: https://www.macupdate.com/app/mac/9980/gpl-ghostscript
    brew install imagemagick
    pip install Wand==0.3.5

Once fully started, you should see a message indicating the address of your geonode.
The default username and password are ``admin`` and ``admin``::

  Development Geonode is running at http://localhost:8000/
  To stop the GeoNode machine run:
  paver stop

  Or quit the server by pressing
  CTRL-C to shut down

Before starting GeoNode (paver start), you could test your installation by running tests::

    paver test
    paver test_integration

In case you want to build yourself the documentation, you need to install Sphinx and the run 'make html' from within the docs directory::

    pip install Sphinx
    pip install sphinx_rtd_theme
    cd docs
    make html

You can eventually generate a pdf containing the whole documentation set. For this purpose, if using Ubuntu you will need to install the texlive-full package::

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

Development Roadmap
===================

Geonode's development roadmap is documented in a series of Geonode Improvement Projects (GNIPS).
They are documented here: https://github.com/GeoNode/geonode/wiki/GeoNode-Improvement-Proposals.
GNIPS are considered to be large undertakings which will add a large amount of features to the project.
As such they are the topic of community dicussion and guidance.
The community discusses these on the developer mailing list: http://lists.osgeo.org/pipermail/geonode-devel/
Github issues tracks features and bugs, for new developers the tag 'easy-pick' indicates an
issue that should be relatively easy for new developers to understand and complete. Once you have completed an issue
a pull request should be submitted. This will then be reviewed by the community.

GPL License
===========

GeoNode is Copyright 2016 Open Source Geospatial Foundation (OSGeo).

GeoNode is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GeoNode is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with GeoNode.  If not, see <http://www.gnu.org/licenses/>.
