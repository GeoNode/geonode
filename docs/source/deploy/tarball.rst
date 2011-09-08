Deploying from the GeoNode tar.gz Distribution
==============================================

The most generic package provided by the GeoNode project is the tar.gz ("tarball").
This is the most customizable, but also the most difficult, installation mechanism for GeoNode.
Some platforms have more convenient packages available, so check at :doc:`/deployment` to see whether one is available for your OS before going through these steps.

What's in the Package?
----------------------

This packaging simply contains the Java and Django web application code for GeoNode, and requires some external software installed (a WSGI-compliant webserver and a Java application container) to complete the GeoNode platform.
Some scripts are included to assist in configuring this external software in a default recommended configuration.
These scripts have been tested on Ubuntu, please review them carefully before using them on another operating system.

.. note:: 

    While we intend to provide a detailed, accurate explanation of the
    installation process, it may become out of date.  If you run into problems
    with the process described in this document, please don't hesitate to let
    the GeoNode team know so we can keep it up to date.

The stack used is:

* *Servlet Container*: Apache Tomcat

* *Static File Server*: Apache httpd

* *Python/WSGI Container*: mod_wsgi

* *Django Database*: PostgresQL

Download GeoNode Release Archive
--------------------------------
You get the latest GeoNode release from http://dev.geonode.org/release/ or the `GeoNode project wiki <http://dev.geonode.org/trac/>`_ .

You can unpack it like::

   $ tar xvzf GeoNode-1.1.tar.gz
   GeoNode-1.1/geonetwork.war
   GeoNode-1.1/geonode-webapp.pybundle
   GeoNode-1.1/geoserver.war
   GeoNode-1.1/bootstrap.py
   GeoNode-1.1/deploy-libs.txt
   GeoNode-1.1/install.sh
   GeoNode-1.1/support/

This tarball comes with an install script and a directory with supporting config files.

Installing Dependencies
-----------------------

As mentioned above, you must have some external software installed before you can setup GeoNode.
This includes:

* A Python interpreter

* A Java Runtime Environment (JRE)

* Apache Tomcat servlet container
 
* Python development libraries

* PostgresQL database

* The GDAL, GEOS, and OGR geospatial software libraries

For convenience, appropriate commands to retrieve these dependencies on different OS's are listed below:

Ubuntu
......

.. code-block:: bash

    $ sudo apt-get install python python-support python-dev python-virtualenv \
        openjdk-6-jre tomcat6 postgresql-8.4 gcc patch zip python-imaging \
        python-reportlab gdal-bin libgeos-dev python-urlgrabber \
        python-pastescript gettext postgresql-contrib \
        postgresql-8.4-postgis,libpq-dev unzip libjpeg-dev libpng-dev
        python-gdal \ libproj-dev python-psycopg2 apache2 libapache2-mod-wsgi

Installation
------------

1) The installer script has a configuration file associated with it which allows you to provide the details of your installation, such as where your webserver looks for documents.
   These vary from distribution to distribution - for example Ubuntu systems keep Apache site configurations in /etc/apache2/sites-available/ while CentOS uses /etc/httpd/conf.d/; and of course if you are using custom-built software you may need a totally separate configuration.
   Samples for common platforms are included, please check for one that matches your distribution.
   If it is not available or you would like to install to a custom directory, the configurations are simple shell scripts and you can copy and modify one to meet your needs.

   More instructions can be found in the README distributed with the release as well as the pointer to the documentation page about configuring GeoNode for production after it has been installed.

2) After unpacking the .tar.gz archive and locating or constructing a configuration for the install, you can install GeoNode by simply running the script (usually it is necessary to run it as a root user to allow adding files to system directories.)
   For example, on ubuntu you can use the provided configuration in support/config-ubuntu.sh ::

    $ cd GeoNode-1.1/
    $ sudo ./install.sh support/config-ubuntu.sh

Manual Installation
===================
This section is mostly intended for packagers working on installers for GeoNode on new platforms.
If you simply want a customized installation of GeoNode, we recommend reviewing and modifying the installer script included with GeoNode instead of starting "from scratch."

The key points of setting up a GeoNode installation are as follows:

1) *Set up applications.*
   The GeoServer and GeoNetwork web applications must be served using a Java Servlet container; two popular and free containers are Jetty and Tomcat.
   Typically a Java web application can be deployed by simply copying the .war file into the appropriate place.
   The Django frontend can be served in a few ways, one of the most performant is Apache httpd with mod_wsgi installed.
   Regardless of the specific deployment technology you choose, GeoNode includes a Pip bundle containing its Python dependencies; once you install Python and Pip for your platform you can install the rest of GeoNode's Python dependencies using ``pip install geonode-webapp.pybundle``.
   The Django project has further documentation on how to serve Django applications at https://docs.djangoproject.com/en/1.2/howto/deployment/ .
   You will also need a web server capable of simply serving static files; if you are using Apache httpd it can serve this purpose as well.

2) *Configure them to talk to each other*.
   GeoNode's components communicate over HTTP, and therefore must know each others' URLs.
   Two settings files contain the settings relevant to most GeoNode deployments:

   * GeoServer's ``WEB-INF/web.xml`` file; this will be in the "exploded war" directory created when your servlet container deploys the GeoServer application.
     You can edit it in the text editor of your choice, add a config-param element with the name "GEONODE_BASE_URL" and the value being the base URL of your site.

   * The Django application's ``settings.py`` file; this will be in the directory where you installed the Django application under ``src/GeoNodePy/settings.py``.
     In order to simplify upgrades, it is recommended to create a new file next to it named ``local_settings.py`` for your own settings; any settings in this file will override the default ones in the settings file included with GeoNode.
     The settings to use here are:
    
     * ``SITEURL`` the base URL for all pages in your GeoNode site, for example `http://example.com/`

     * ``GEOSERVER_BASE_URL`` the base URL for the GeoServer for your GeoNode site, for example `http://example.com/geoserver/`.
       Some features of GeoNode require you to set up a web proxy so that GeoServer and the Django application are on the same domain ("example.com" in this example.).

     * ``GEONETWORK_BASE_URL`` the base URL for the GeoNetwork for your GeoNode site, for example `http:/example.com/geonetwork/`.

     * ``GEONODE_CLIENT_LOCATION`` the URL where the static files for GeoNode are published, for example `http://example.com/media/`.  These files can be found on disk in the directory where you installed the Django application under :file:src/GeoNodePy/geonode/media/ .
