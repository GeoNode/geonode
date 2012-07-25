=========
 GeoNode
=========

If you just want to try GeoNode, it is recommended to use Ubuntu 10.04 and install the latest stable release::

    sudo add-apt-repository ppa:geonode/release
    sudo apt-get update
    sudo apt-get install geonode

If instead, you are interested in doing development on the source code, here are the instructions for Ubuntu 12.04::


    # Python native dependencies
    sudo apt-get install python-virtualenv python-imaging python-lxml
     
    # Java dependencies
    sudo apt-get install -y --force-yes openjdk-6-jdk ant maven2 --no-install-recommends
    
    # Supporting tools
    sudo apt-get install -y  git gettext
    
    # Create virtualenv and activate it
    virtualenv venv --system-site-packages
    source venv/bin/activate
    
    # Clone GeoNode and switch to dev branch
    git clone https://github.com/GeoNode/geonode.git -b dev
    
    # Install GeoNode in the local virtualenv
    pip install -e geonode --use-mirrors

    cd geonode

    # Compile GeoServer
    paver setup
    
    # Start the servers
    paver start

Windows Development Build Instructions
    Prerequisites:
    # Java JDK
    # Python 2.6+
    # ant (bin directory must be on system PATH)
    # maven2 (bin directory must be on system PATH)
    # Python distutils (easy_install)
    # git

    # Install and configure from the windows command prompt
    If you don't already have python virtualenv installed, then do it now:
         easy_install virtualenv

    # Create virtualenv and activate it
    cd <Directory to install the virtualenv & geonode into>
    virtualenv venv
    venv/scripts/activate

    # Install Python native dependencies
    easy_install PIL lxml==2.3
    # this command will look for and install binary distributions (pip install will attempt to build and fail)

    # Clone GeoNode and switch to dev branch
    git clone https://github.com/GeoNode/geonode.git -b dev
    
    # Install GeoNode in the local virtualenv
    pip install -e geonode --use-mirrors

    cd geonode

    # Compile GeoServer
    paver setup
    
    # Start the servers
    paver start <-- This WON'T work on windows without changes to pavement.py 
                    and a windows batch script for starting jetty    


Once fully started, you should see a message indicating the address of your geonode.
The default username and password are ``admin`` and ``admin``::
  
  Development GeoNode is running at http://localhost:8000/
  The GeoNode is an unstoppable machine
  Press CTRL-C to shut down


.. note:: 

  When running ``virtualenv venv`` the ``--system-site-packages`` option is
  not required.  If not enabled, the bootstrap script will sandbox your virtual
  environment from any packages that are installed in the system, useful if
  you have incompatible versions of libraries such as Django installed
  system-wide.  On the other hand, most of the times it is useful to use a version of
  the Python Imaging Library provided by your operating system
  vendor, or packaged other than on PyPI.  When in doubt, however, just leave
  this option out.


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
