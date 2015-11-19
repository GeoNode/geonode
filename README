.. image:: https://secure.travis-ci.org/GeoNode/geonode.png
    :alt: Build Status
    :target: http://travis-ci.org/GeoNode/geonode


GeoNode Support
===============

To get support, give feedbacks and suggestions please use the GeoNode official channels, the users mailing list: http://lists.osgeo.org/pipermail/geonode-users/ and the developers mailing list: http://lists.osgeo.org/pipermail/geonode-devel/.

This repository is used to track code changes and GeoNode issues, please DON'T open new issues to ask for support.


GeoNode Installation
====================

If you just want to try GeoNode, it is recommended to use Ubuntu 12.04 and install the python software properties.::

    sudo apt-get install python-software-properties

For 12.04 with python software properties installed, install the latest stable release of GeoNode.::

    sudo add-apt-repository ppa:geonode/release
    sudo apt-get update
    sudo apt-get install geonode

If instead, you are interested in doing development on the source code, here are the instructions: http://docs.geonode.org/en/master/tutorials/devel/install_devmode/index.html#install-devmode.

Docker Usage
If you want to use Docker you can now::

    # build the docker container
    docker build -t geonode .

    # run the docker container
    docker run -d -p 8111:8000 -p 8181:8080 geonode

Or if you use fig::

    # build the container
    fig build

    # run the container
    fig up

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
    
    # Start the servers
    paver start

Windows Development Build Instructions::


    Prerequisites:
    # Java JDK
    # Python 2.7
    # ant (bin directory must be on system PATH)
    # maven2 (bin directory must be on system PATH)
    # Python distutils (easy_install)
    # GDAL Core Libraries
    # git

    # Install and configure from the windows command prompt
    If you don't already have python virtualenv installed, then do it now:
    easy_install virtualenv

    # Create virtualenv and activate it
    cd <Directory to install the virtualenv & geonode into>
    virtualenv venv
    venv\scripts\activate

    # Clone GeoNode
    git clone https://github.com/GeoNode/geonode.git
    
    # Install compiled packages for Python 2.7 Win32
    cd geonode
    pip install paver
    paver win_install_deps
    
    # Install GeoNode in the local virtualenv
    pip install -e . --use-mirrors
    
    # Compile GeoServer
    paver setup
    
    # Start the servers
    paver start --java_path=C:/path/to/java/bin/java.exe

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

GeoNode is Copyright 2010 OpenPlans.

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
