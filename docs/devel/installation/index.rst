How to Install GeoNode for development
======================================

Summary of installation 
.......................
This section demonstrates a summarization of the steps to be followed in order to install GeoNode for development using Ubuntu 18.04. The following steps will be customised to fit both GeoNode-Project and GeoNode-Core for development purpose.

The steps to be followed are:
.............................
1- Install build tools and libraries
2- Install dependencies and supporting tools
3- Setup Python virtual environment
4- Download/Clone GeoNode from Github
5- Install and start Geoserver
6- Start GeoNode

.. note:: The following commands/steps will be executed on your terminal 

.. warning:: If you have a running GeoNode service, you will need to stop it before starting the following steps. To stop GeoNode you will need to run:

:: 
service apahe2 stop   # or your installed server
service tomcat7 stop  # or your version of tomcat 


Install GeoNode-Project for development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Geonode-Project gives the user flexibility to customize the installation of the GeoNode. The repository of geonode-project contains a minimal set of files following the structure of a django-project. Geonode itself will be installed as a requirement of your project. Inside the project structure it is possible to extend, replace or modify all geonode componentse (e.g. css and other static files, templates, models..) and even register new django apps without touching the original Geonode code.

Installation steps
..................
1- Install build tools and libraries

::
$ sudo apt-get install -y build-essential libxml2-dev libxslt1-dev libpq-dev zlib1g-dev




Install GeoNode-Core for development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


