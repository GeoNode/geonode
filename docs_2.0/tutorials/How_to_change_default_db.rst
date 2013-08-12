============================
How to change the default db
============================

.. todo:: install postgres, install postgis, how to change! toctree machen mit drei unterpunkten

Installation of Postgresql-9.2 on Ubuntu 12.04 
==============================================

Installation
------------

The Installation of Postgresql-9.2 on Ubuntu 12.04 includes two main steps (Generelly, this installation should work for each version of Postgresql!). 



*Step 1*

Create an empty file called *pgdg.list* placed in /etc/apt/sources.list.d/, using these commands::

  cd /etc/apt/sources.list.d/
	
	sudo touch pgdg.list
  
Now the following line has to be included the *pgdg.list* file.

	deb http://apt.postgresql.org/pub/repos/apt/ codename-pgdg main
	
Instead of *codename* write the name of your system. If you do not know this, type

	 lsb_release -c

This will return you the name of your system.

.. warning::
Make sure that you have changed *codename* to the name of your system before you copy the link in the next step!

Now open the *pgdg.list* file using e.g.::

	gksu gedit pdgd.list
	
and copy deb `http://apt.postgresql.org/pub/repos/apt/ codename-pgdg main` into it.


*Step 2*

Now you have to import the repository key from their website. Use the following command to do so:

	wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -

After that you have to update the package lists using

	sudo apt-get update
	
and then you can install postgresql-9.2 and pgadmin3 (if needed)

	sudo apt-get install postgresql-9.2 pgadmin3


Configuration
-------------

**General**

*Step 1 – Change password*

First of all you have to set a new password for the superuser *postgres*. In order to do so, type the following command line into your terminal:

	sudo -u postgres psql postgres
	
Now you are in *psql*, the command interface for postgresql, and in the database *postgres*. In your terminal it looks like this at the moment:

	postgres=#

To change your password, type

	\password postgres
	
and type your new password when asked for it.



*Step 2 – Create a database* (for testing)

If you want to create a db, posgresql has to know, which user you are. Therefore you have to type `-u username` in front of the command `createdb`. If you type the following, it means that you as the user *postgres* want to create a database wich is called *mydb*.

	sudo -u postgres createdb mydb


**For geonode**

*Remark*: If you want to use the *postgis extension* for *postgresql* then you may follow the instructions from this site .... .
If you do not need that (from the beginning) you can follow this instruction. You can even add the *posgis extension* later following the steps from the section *Alternative*. Anyway it is recommended to do the common version. 


*Step 1 – Create a new user (geonode)*

In order to use postgresql in geonode, you have to create a new user *geonode*, which is the owner of a new database, also called *geonode*. So first create a new user by typing

	sudo -u postgres createuser -P geonode

This means, that you as the user *postgres* create a new user called *geonode*. `-P` indicates, that this user will have a password (*geonode*). 



*Step 2 - Create new database*

After creating the new user you can create the db *geonode*:

	sudo -u postgres createdb -O geonode geonode
	
	
PostGis2.0.3 Installation on Ubuntu 12.04
=========================================

**Step 1 – Install dependencies**

Before you can install PostGis 2.0.3, some dependencies have to be installed first. You can do this by using the Linux command *apt-get*. It is recommended to install postgresql-9.2 before you install PostGis 2.0.3. For the installation guide of postgresql-9.2 see ... .

Now the first step is to type the following command into your terminal to install all dependencies:

    sudo apt-get install build-essential postgresql-server-dev-9.2 libxml2-dev libproj-dev libjson0-dev xsltproc docbook-xsl docbook-mathml libgdal1-dev

*Remark*: libgdal1-dev is needed for raster support and is required if you want to build the postgresql extension!



**Step 2 – Build Geos 3.3.2 or higher**

GEOS is used for the topology support and because Postgis 2.0 requires a GEOS version 3.3.2 or higher, you have to build this before you can install postgis itself. (genereally Ubuntu comes with an GEOS version lower than 3.3.2!) Download your favourite version of geos (has to be 3.3.2 or higher!) using the following command line:

    wget http://download.osgeo.org/geos/geos-3.3.8.tar.bz2

Unpack it and go to the unpacked folder::

    tar xvfj geos-3.3.8.tar.bz2
    cd geos-3.3.8

Now you can install geos by using the following command lines (this process may take a while)

    ./configure
    make
    sudo make install
    cd ..


**Step 3 – Install postgis**

The following steps are almost the same like instructed in *Step 2*. Download postgis 2.0.3, unpack it and go to unpacked folder.

    wget http://download.osgeo.org/postgis/source/postgis-2.0.3.tar.gz
    tar xfvz postgis-2.0.3.tar.gz
    cd postgis-2.0.3

Now postgis can be installed:

    ./configure
    make
    sudo make install
    sudo ldconfig
    sudo make comments-install

*Remark*: PostGIS 2.0.3 can be configured to disable topology or raster components using the configure flags

    --without-raster

and/or

    --without-topology.

The default is to build both. Note that the raster component is required for the extension installation method for postgresql!



Create the postgis extension for postgresql
-------------------------------------------

**Common way**

The best way to install the postgis extension is by using templates. After downloading and installing postgresql and postgis you create a database called template_postigsxxx (xxx should be replaced by your version of postgis; in this case postgis 2.0.3 was used).

    sudo -u postgres createdb template_postgis203

Before installing the extension you have to log in to the database

    psql template_postgis203

and now you can create the extension

    create extension postigs;

*Remark*: Do not forget the semicolon at the end! Otherwise this statement will have no effect!

Now you can easily create a new database wich automatically has the postgis extension as well, e.g create a new database called geonode like this

    sudo -u postgres createdb -T template_postgis203 geonode

(Remark: -T stands for template)



**Alternative**

If you already created a db called *geonode*, then you can use this alternative to create the extension for postigs.

By typing

    sudo su postgres

you log in as the user *postgres*.

By using the following command line

    psql geonode

you log in to the database *geonode*.

To install the posgis extension type

    create extension postgis;

Now you should have successfully installed the postgis extension in your geonode database.


How to change the default db to postgres
========================================

If you have installed Geonode 2.0 in developing mode, then Geonode will use *sqlite3* as default database (set in *settings.py*). This section will show you how to exchange the default database with a postgresql database. 

If you haven't installed postgresql so far, you can use this installation guide: --inlcude link!

.. note:: If you followed the installation guide from our website, you should already have created a geonode user and database!

Create geonode user and database
--------------------------------

In order to use a postgresql database for geonode, you have to create a user called *geonode* (with password *geonode*), as well as a database called *geonode*.

Open a terminal and type::

	sudo -u postgres createuser -P geonode

Now you will be asked to enter a password. This must be *geonode*.

To create the db::

	sudo -u postgres createdb -O geonode geonode

This creates a db called *geonode* with its owner *geonode*.

Change authentication method
----------------------------

In the postgres config path, */etc/postgresql/9.2/main*, you should find the file *pg_hba.conf*.  
This file has to be edited in order to allow the geonode user to have access to the database (?). 
Therfore change the directory to this file and open it::  

	cd /etc/postgresql/9.2/main
	sudo vi pg_hba.conf

The file should contain the following default settings until now:

.. image:: img/pg_hba_conf.png


First, add this entry::
	
	#Type	DATABASE	USER	ADDRESS		METHOD
	host	geonode		geonode	127.0.0.1/32	md5

(Do I really have to add this????)
and then set the authentication method of the following entry from *peer* to *trust*::

.. image:: img/pg_hba_detail.png

::
	#TYPE   DATABASE	USER	METHOD
	local	all		all	trust

(Should this method be used???)

After changing this file, the postgres service has to be restarted. This is essential, because otherwise the changed configurations won't
be considered!

To restart the postgresql server type::

	sudo service postgresql restart

or::
	
	sudo /etc/init.d/postgresql restart

Both methods should work!

(I used:
	sudo service postgresql stop
	sudo service postgresql start
)

Setup local settings
--------------------

The next step is to set the local settings. In the directory ../geonode/geonode a file called *local_settings.py.sample* exists. It includes all the settings to change the default db from *sqlite3* to *postgresql*. Rename the file to *local_settings.py*::

	sudo mv local_settings.py.sample local_settings.py

Install psycopg2
----------------

If you do not already have it on your machine, it is neccessary to install psycopg2, the postgresql adapter for Python programming language. 
But, be sure that you are working in your virtualenv, otherwise you will create a permission problem!! Thus activate your virtualenv first::

	cd /.venvs/geonode/bin

	source activate

	cd

	pip install psycopg2

Start developing servers
------------------------

Now you should be able to start the servers using::

	paver start


