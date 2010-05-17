Getting Started with GeoNode
============================

The GeoNode project provides some tools for you to use in quickly and
conveniently setting up your own GeoNode.  These are provided in the form of 

* A set of reusable applications for the Django web framework
* A customized build of the GeoServer geographic data server with plugins to
  ease interaction with Django
* A customized build of the GeoNetwork geographic data catalog with a
  simplified  metadata schema

Building from source
--------------------

GeoNode's source tree is managed using the Subversion version control software.
Since it mixes Java and Python components, it requires both a Java Virtual
Machine (JVM) and a Python interpreter to build.  Apache's Maven build tool is
also needed for the Java portions when building from scratch.  Or, in checklist form, you'll need to have installed:

* The Subversion command-line client.  If you like, you can also use one of the
  many graphical clients, but you will need the command-line client as part of
  the build.
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
   
     $ svn checkout http://svn.opengeo.org/CAPRA/GeoNode/trunk/ GeoNode/

#. Change directories into the GeoNode source directory and use the
   ``bootstrap.py`` script to set up a virtualenv sandbox and install the
   GeoNode dependencies into it::

     $ cd GeoNode && python bootstrap.py

#. Since GeoNode uses virtualenv to isolate its python
   modules from the wider system, you must "activate" the virtualenv before
   using GeoNode-related commands::

     $ . bin/activate # for Linux, Mac, and other Unix-like OS's

   ::

     C:\> Scripts/activate.bat ; for Windows

#. Now you should have GeoNode and its dependencies set up and ready to run in
   development mode. (See some other section of this manual for information
   about deployment.)  The command to start up a development server is::

     $ django-admin.py runserver --settings=geonode.settings

   This sets up the GeoNode demo site, which includes a map editor and data
   browsing tools in a fairly generic configuration.


* Navigating the development environment

  * components: geoserver, geonetwork, geoext, django
  * your own site sources

* Using the development kit
