============================
How to change the default db
============================

some more text here...

.. todo:: install postgres, install postgis, how to change! toctree machen mit drei unterpunkten

	  sollte so aussehen:
	  	- installation
	  		- postgres
	  		- postgis
	  		- apache2
	  		- tomcat
	  	- configuration
	  		- create extension
	  		- create user and db => db settings
	  		- apache config
	  		- tomcat and geoserver

If you´ve installed geonode in developing mode, geonode uses the *sqlite3* database as default. This tutorial will guide you through the steps that have be done in order to use *postgresql* instaed of *sqlite3*.

Installation
============

Installation of Postgresql-9.2 on Ubuntu 12.04 
----------------------------------------------

First of all postgresql has to be installed. If you already have it running on your machine, you might skip this part and go further to LINK.

Installation
------------

The Installation of Postgresql-9.2 on Ubuntu 12.04 includes two main steps (Generelly, this installation should work for every version of Postgresql!). 

#. Create an empty file called *pgdg.list* placed in ``/etc/apt/sources.list.d/``, using these commands
   
   .. code-block:: console

   	$ cd /etc/apt/sources.list.d/
   	$ sudo touch pgdg.list

   The following line has to be included into the *pgdg.list* file.

   .. code-block:: console

	   deb http://apt.postgresql.org/pub/repos/apt/ codename-pgdg main
	
   Instead of *codename* write the name of your system. If you do not know this, type

   .. code-block:: console

	   $ lsb_release -c

   This will return you the name of your system.

   .. warning:: Make sure that you have changed *codename* to the name of your system before you copy the link in the next step!

   Thus open the *pgdg.list* file 
 
   .. code-block:: console

	   $ sudo gedit pdgd.list
	
   and include the line from above.

#. The next step is to import the repository key from the postgresql website. Use the following command to do so:

   .. code-block:: console

	   $ wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -

   Afterwards you have to update the package lists using

   .. code-block:: console

	   $ sudo apt-get update
	
   Now you should be able to install postgresql-9.2 and pgadmin3 (if needed)

   .. code-block:: console

	   $ sudo apt-get install postgresql-9.2 pgadmin3

Configuration
-------------

Before we start configuring postgres to work with geonode, we´ll do two initial configuration steps.

#. **Change superuser password**

   First of all you have to set a new password for the superuser *postgres*. In order to do so, type the following command line into your terminal:

   .. code-block:: console
   
	   $ sudo -u postgres psql postgres
	
   Now you are in *psql*, the command interface for postgresql, and in the database *postgres*. In your terminal it looks like this at the moment::
   
	   postgres=#

   To change your password, type::

	   $ \password postgres
	
   and set your new password when asked for it.
   
#. **Create a database** (for testing)

   If you want to create a db, posgresql has to know, which user you are. Therefore you have to type `-u username` in front of the command `createdb`. If you type the following, it means that you as the user *postgres* want to create a database wich is called *mydb*.
   
   .. code-block:: console
   
	$ sudo -u postgres createdb mydb
   
Installation of PostGis2.0.3 on Ubuntu 12.04
============================================

#. **Install dependencies**
   
   Before you can install PostGis 2.0.3, some dependencies have to be installed first. You can do this by using the Linux command *apt-get*. 

   .. code-block:: console

	$ sudo apt-get install build-essential postgresql-server-dev-9.2 libxml2-dev libproj-dev libjson0-dev xsltproc docbook-xsl docbook-mathml libgdal1-dev

   .. note:: ``libgdal1-dev`` is needed for raster support and is required if you want to build the postgresql extension!

#. **Build Geos 3.3.2 or higher**

   GEOS is used for the topology support and because Postgis 2.0 requires a GEOS version 3.3.2 or higher, you have to build this before you can install postgis itself. (genereally Ubuntu comes with an GEOS version lower than 3.3.2!) Download your favourite version of geos (has to be 3.3.2 or higher!) using the following command line:

   .. code-block:: console
   
       $ wget http://download.osgeo.org/geos/geos-3.3.8.tar.bz2

   Unpack it and go to the unpacked folder:

   .. code-block:: console
   
      $ tar xvfj geos-3.3.8.tar.bz2
      $ cd geos-3.3.8

   Now you can install geos by using the following command lines (this process may take a while)

   .. code-block:: console
   
       $ ./configure
       $ make
       $ sudo make install
       $ cd ..


#. **Install postgis**

   The following steps are almost the same like instructed lllll. Download postgis 2.0.3, unpack it and go to unpacked folder.

   .. code-block:: console
   
	   $ wget http://download.osgeo.org/postgis/source/postgis-2.0.3.tar.gz
           $ tar xfvz postgis-2.0.3.tar.gz
           $ cd postgis-2.0.3

   Now postgis can be installed:

   .. code-block:: console
   
	   $ ./configure
           $ make
           $ sudo make install
           $ sudo ldconfig
           $ sudo make comments-install

   .. note:: PostGIS 2.0.3 can be configured to disable topology or raster components using the configure flags ``--without-raster`` and/or ``--without-topology``. The default is to build both. Note that the raster component is required for the extension installation method for postgresql!

Create the postgis extension for postgresql
-------------------------------------------

Now we´ve installed postgres and postgis we want to create the postgis extension for postgresql. The best way to do so is by using templates. Therefore we will now create a database called **template_postigsxxx** (xxx should be replaced by your version of postgis; in this case postgis 2.0.3 was used).

.. code-block:: console
   
	$ sudo -u postgres createdb template_postgis203

Before installing the extension you have to log in to the database

.. code-block:: console
   
	$ psql template_postgis203

and now you can create the extension

.. code-block:: console

	$ create extension postigs;

.. note:: Do not forget the semicolon at the end, otherwise this statement will have no effect!

We can now use this template to easily create a new database wich automatically has the postgis extension as well!

How to configure geonode to user postgresql
===========================================

We have now successfully installed postgresql and postgis and want to configure geonode to user postgresql instead of sqlite3.

Create geonode user and database
--------------------------------

In order to use a postgresql database for geonode, you have to create a user called *geonode* (with password *geonode*), as well as a database called *geonode*.

Open a terminal and type:

.. code-block:: console

	$ sudo -u postgres createuser -P geonode

Now you will be asked to enter a password. This must be *geonode*.

To create the db:

.. code-block:: console

   	$ sudo -u postgres createdb -T template_postgis203 -O geonode geonode
   	
This creates a db called *geonode* (which automatically has the postgis extension as well!) with its owner *geonode*.

Change authentication method
----------------------------

In the postgres config path, */etc/postgresql/9.2/main*, you should find the file *pg_hba.conf*. This file has to be edited in order to allow the geonode user to have access to the database (?). Therfore change the directory to this file and open it  

.. code-block:: console

	$ cd /etc/postgresql/9.2/main
	$ sudo vi pg_hba.conf

The file should contain the following default settings until now:

.. image:: img/pg_hba_conf.png

and then set the authentication method of the following entry from *peer* to *md5*::

	#TYPE   DATABASE	USER	METHOD
	local	all		all	md5

After changing this file, the postgres service has to be restarted. This is essential, because otherwise the changed configurations won't be considered!

To restart the postgresql server type

.. code-block:: console

	$ sudo service postgresql restart

Setup local settings
--------------------

The next step is to set the local settings. In the directory ../geonode/geonode a file called *local_settings.py.sample* exists. It includes all the settings to change the default db from *sqlite3* to *postgresql*. Rename the file to *local_settings.py*.

.. code-block:: console

	$ sudo mv local_settings.py.sample local_settings.py

Install psycopg2
----------------

If you do not already have it on your machine, it is neccessary to install *psycopg2*, the postgresql adapter for Python programming language. But, be sure that you are working in your virtualenv, otherwise you will create a permission problem!! Thus activate your virtualenv first

.. code-block:: console

	$ source home/user/.venvs/geonode/bin/activate
	$ cd
	$ pip install psycopg2

Start developing servers
------------------------

To check whether your changes have been admitted, try to start the developer servers with:

.. code-block:: console

	$ paver start



.. todo:: the following has to be added somewhere!

	   *Alternative**

	    If you already created a db called *geonode*, then you can use this alternative to create the extension for postigs.

            By typing

            .. code-block:: console

            $ sudo su postgres

            you log in as the user *postgres*.
 
            By using the following command line

            .. code-block:: console

            $ psql geonode

            you log in to the database *geonode*.

            To install the posgis extension type

            .. code-block:: console

            $ create extension postgis;

            Now you should have successfully installed the postgis extension in your geonode database.
