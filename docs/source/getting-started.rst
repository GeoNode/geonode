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

GeoNode's source tree is managed using the `git <http://git-scm.org/>`_ version control software.
Since it mixes `Java <http://java.com/>`_ and `Python <http://python.org/>`_ components, it requires both a Java Virtual Machine (JVM) and a Python interpreter to build.
Apache's `Maven <http://maven.apache.org/>`_ build tool is also needed for the Java portions when building from scratch.
Or, in checklist form, you'll need to have installed:

* The git command-line client.
* A Java Virtual Machine, at least version 1.5.
  The latest from Oracle is recommended for performance reasons.
* A Python interpreter, at least version 2.6.2.  Since the Python APIs are
  subject to revision between minor versions, it is recommended that you stick
  with the 2.6.x series.
* Apache's Maven build tool, at least version 2.0.10.  Many Linux distributions
  modify Maven in ways that cause problems for the build, so it is recommended
  that you download and install directly from the Apache website.
  GeoNode is not yet compatible with Maven 3.x, so ensure that you are using 

All other dependencies will be fetched automatically as part of the build
process.  So, here are the steps to follow:

#. Fetch the latest version of the GeoNode sources by using the command::
   
     $ git clone git://github.com/GeoNode/geonode.git 

#. The GeoNode git repository includes a "bootstrap" script which sets up a python `virtualenv <http://virtualenv.org/>`_ and installs `Paver <http://paver.github.com/paver/>`_, the build tool used for GeoNode.
   To run it, change directories into the new working directory and execute with python::

     $ cd geonode && python bootstrap.py

#. Now, "activate" the virtualenv to make the libraries and scripts installed into it available. 
   If all goes well, this should add the name of the directory to your shell prompt so you can tell at a glance the virtualenv is in effect::

     $ source bin/activate
     (geonode) $

#. With the virtualenv activated, you can now run paver.
   This step will take a while and download further dependencies for GeoNode.

   .. code-block:: bash

      (geonode) $ paver build

#. Now, set up a user account in the development site.
   Some operations in GeoNode require that there be at least one administrative user, so you may get odd errors if you skip this step.

   .. code-block:: bash
   
      (geonode) $ django-admin.py createsuperuser --settings=geonode.settings

   There are a couple of things going on here, so let's stop and explain a bit.
   ``django-admin.py`` is a tool that is part of the Django web framework, used for certain administrative tasks.
   The general way that ``django-admin.py`` is used is to specify the *name* of an operation, followed by any further information that operation may need.
   Here, the operation is ``createsuperuser`` and the additional information is ``--settings=geonode.settings``, which helps Django find our project configuration.
   Normally Django would be able to find our settings without us telling it explicitly where they are, but in GeoNode we put the Python code in a subdirectory to separate it from the Java code, so Django needs a little help.  
   You will need to specify the settings for each django-admin.py command you use.
   If you find yourself doing this a lot, you may find it useful to set the ``DJANGO_SETTINGS_MODULE`` environment variable instead::

      (geonode) $ export DJANGO_SETTINGS_MODULE=geonode.settings
      (geonode) $ django-admin.py createsuperuser

   .. seealso::

      The Django project has lots of helpful documentation for working on Django projects.
      For more information about the ``django-admin.py`` tool, see https://docs.djangoproject.com/en/1.2/ref/django-admin/ .

#. Now that all the libraries and scripts are set up, and a user account is prepared, you can start up the site!
   Since GeoNode websites incorporate web services written in both Java and Python, this actually requires two servers.
   So, two terminal sessions are required for this step.
   For the Java components, change directories to the ``src/geoserver-geonode-ext/`` directory and use the startup script in that directory::

      $ cd src/geoserver-geonode-ext/
      $ sh startup.sh

   For the Python components, you can run from the working directory::

      (geonode) $ paster serve --reload shared/dev-paste.ini

   If both of the above commands run without error, you should now have a working GeoNode site at http://localhost:8000/ .
   As requests come in, debugging information will show up in both terminal windows.

Keep reading for some more information about working on GeoNode.

Common Development Tasks
------------------------------

Using Paver
...........

``paver`` is the build tool used for GeoNode development.
The build tasks for GeoNode are all defined in the ``pavement.py`` file in the base of the GeoNode working directory.

You can list all available paver tasks with the ``help`` task::

   (geonode) $ paver help

A few tasks are of particular interest, however.

Resetting the Database
......................

Sometimes it is useful to clear out GeoNode's data (for example, establishing a known state before running tests.)
This requires resetting the database for the Django application, the GeoServer data directory, and the GeoNetwork search index.
Resetting the Django application can be accomplished by simply removing the ``development.db`` file and creating a fresh one with ``django-admin.py``::

   (geonode) $ rm development.db
   (geonode) $ django-admin.py syncdb --settings=geonode.settings

Then, this command will reset the GeoServer and GeoNetwork data back to a known-good sample data set::

   (geonode) $ paver clean=true setup_webapps

Producing Release Archives
..........................

There is a paver task to create "release archives" of GeoNode, suitable for :doc:`production deployments </deployment>`::

   (geonode) $ paver name=ReleaseName make_release

Navigating the Source Directory
-------------------------------

The source tree you just set up contains all the different components of the
GeoNode.

  * ``pavement.py`` is a build script that produces development kits and
    manages some other tasks.  Use the ``paver`` command to execute build
    tasks.  ``paver help`` provides a list of the available tasks and their descriptions.

  * ``src/`` contains sources for the GeoNode Python and Java components

     * ``src/geoserver-geonode-ext/`` contains some GeoServer extensions to assist with interaction between GeoServer and Django.  Instead of an extension archive, the build script for this project produces a full GeoServer package with the GeoNode extensions installed and configured.
     * ``src/GeoNodePy/`` contains the Django apps that support GeoNode sites.
  
  * ``shared/`` contains some configurations for the build process (Python
    library dependencies, download paths, etc) and also contains some built
    artifacts.  Consult the source of ``pavement.py`` for some information
    about how these configuration files are used.

  * ``webapps/`` contains GeoNetwork and Intermap for use during development

  * ``gs-data/`` contains a GeoServer data directory for use during development
