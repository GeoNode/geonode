Getting Started with GeoNode Development
========================================

.. note::
    This page describes the steps involved in getting GeoNode set up for
    development purposes.  If you are only interested in *running* GeoNode on a
    public server, see :doc:`/deployment`.

The GeoNode project provides some tools for you to use in quickly and
conveniently setting up your own GeoNode.  These are provided in the form of 

* A set of reusable applications for the Django web framework
* A customized build of the GeoServer geographic data server with plugins to
  ease interaction with Django
* A customized build of the GeoNetwork geographic data catalog with a
  simplified  metadata schema

Building from Source
--------------------

GeoNode's source tree is managed using the Subversion version control software.
Since it mixes Java and Python components, it requires both a Java Virtual
Machine (JVM) and a Python interpreter to build.  Apache's Maven build tool is
also needed for the Java portions when building from scratch.  Or, in checklist form, you'll need to have installed:

* The Subversion command-line client.  If you like, you can also use one of the
  many graphical clients, but you will need the command-line client as part of
  the build.
* The git command-line client.  A graphical client is less important for git
  since the main GeoNode sources are not managed with git; this is solely for
  fetching third-party libraries.
* A Java Virtual Machine, at least version 1.5.  The latest from Sun/Oracle is
  recommended for performance reasons.
* A Python interpreter, at least version 2.6.2.  Since the Python APIs are
  subject to revision between minor versions, it is recommended that you stick
  with the 2.6.x series.
* Apache's Maven build tool, at least version 2.0.10.  Many Linux distributions
  modify Maven in ways that cause problems for the build, so it is recommended
  that you download and install directly from the Apache website.

All other dependencies will be fetched automatically as part of the build
process.  So, here are the steps to follow:

#. Fetch the latest version of the GeoNode sources by using the SVN command::
   
     $ git clone git://github.com/GeoNode/geonode.git 

#. Change directories into the GeoNode source directory and update the git
   submodules used to reference GeoNode's JavaScript dependencies.
   Additionally, use the ``bootstrap.py`` script to set up a virtualenv sandbox
   and install the GeoNode Python dependencies into it::

     $ cd geonode 
     $ git submodule update --init
     $ python bootstrap.py

#. Since GeoNode uses virtualenv to isolate its python
   modules from the wider system, you must "activate" the virtualenv before
   using GeoNode-related commands::

     $ . bin/activate # for Linux, Mac, and other Unix-like OS's

#. Now you should have GeoNode and its dependencies set up and ready to run in
   development mode. (See :doc:`/deployment` for information about deployment.)
   To run GeoNode in development mode you will need to run two separate servers
   for the Java and Python web services.  For the Java services::
    
     $ cd src/geoserver-geonode-dev/
     $ sh startup.sh

   In another terminal, activate the virtualenv again and start up a
   development server with ::

     $ django-admin.py runserver --settings=geonode.settings

   This sets up the GeoNode demo site, which includes a map editor and data
   browsing tools in a fairly generic configuration.


Navigating the Source Directory
-------------------------------

The source tree you just set up contains all the different components of the
GeoNode.

  * ``pavement.py`` is a build script that produces development kits and
    manages some other tasks.  Use the ``paver`` command to execute build
    tasks.  ``paver help`` provides a list of the available tasks.

  * ``src/`` contains sources for several Django components

     * ``src/geonode-client/`` contains some GeoExt components that provide
       interactivity in the Django site
     * ``src/geoserver-geonode-ext/`` contains some GeoServer extensions to
       assist with interaction between GeoServer and Django
     * ``src/GeoNodePy/`` contains the Django apps that support GeoNode sites.
  
  * ``shared/`` contains some configurations for the build process (Python
    library dependencies, download paths, etc) and also contains some built
    artifacts.  Consult the source of ``pavement.py`` for some information
    about how these configuration files are used.

  * ``webapps/`` contains GeoNetwork and Intermap for use during development

  * ``gs-data/`` contains a GeoServer data directory for use during development


#####
Required packages on ubuntu: (besides proj, geos, gdal)
build-essential

python-dev
subversion
git-core
git-svn


sudo apt-add-repository "ppa:ubuntugis/ubuntugis-unstable"
    postgresql-8.4-postgis
    postgresql-server-dev-8.4

sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
    sudo apt-get install sun-java6-jdk

maven2
apache2 libapache2-mod-python libapache2-mod-wsgi


daemon
wget -O /tmp/key http://hudson-ci.org/debian/hudson-ci.org.key
sudo apt-key add /tmp/key
wget -O /tmp/hudson.deb http://hudson-ci.org/latest/debian/hudson.deb
sudo dpkg --install /tmp/hudson.deb
sudo apt-get update
sudo apt-get install hudson



postfix
mailutils
sudo useradd -m -s /bin/bash mailer
sudo passwd mailer
sudo postconf -e "home_mailbox = Maildir/"
sudo postconf -e "mailbox_command = "
sudo /etc/init.d/postfix restart
sudo apt-get install dovecot-imapd dovecot-pop3d
sudo nano /etc/dovecot/dovecot.conf
    protocols = pop3 pop3s imap imaps
    pop3_uidl_format = %08Xu%08Xv

    ## to allow remote access
    listen = *

    ## only set it to no, if the server is to be used with virtual account or internally, else ignore this setting
    disable_plaintext_auth = no

    mail_location = maildir:/home/%u/Maildir
sudo /etc/init.d/dovecat stop
sudo /etc/init.d/dovecat start


FUSE+s3fs
sudo apt-get install autoconf libcurl4-openssl-dev libfuse-dev libselinux1-dev libsepol1-dev libxml2-dev sshfs 
svn checkout http://s3fs.googlecode.com/svn/trunk/ s3fs
	cd /s3fs
	./autogen.sh
	./configure --prfix=/usr
	make
	sudo make install




