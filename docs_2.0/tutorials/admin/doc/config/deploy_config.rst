.. _config.deploy_config:

Configurations
==============

some text here

.. note:: Please note that all the paths are user specific, so they might not coincide with the paths you will have to use!

Change default database
-----------------------

If you have installed geonode in developing mode, it will be running with the sqlite3 db as default. But this can be changed! In order to make geonode to use postgresql just follow the steps from this section.

Create geonode user and database
********************************

First of all a user called *geonode* (with password *geonode*), as well as a database called *geonode* has to be created.

To create the user:

.. code-block:: console

	$ sudo -u postgres createuser -P geonode

Now you will be asked to enter a password. This must be *geonode* (you can change it if you want to, but be aware that you have to edit the local_settings.py if you do so!)

To create the database:

.. code-block:: console

   	$ sudo -u postgres createdb -T template_postgis203 -O geonode geonode
   	
This creates a db called *geonode* (which automatically has the postgis extension as well!) with its owner *geonode*. If you do not have a template with the postgis extension, create one using this guide (LINK).

Change authentication method
****************************

In the postgres config path, */etc/postgresql/9.2/main*, you should find the file *pg_hba.conf*. This file has to be edited in order to allow the geonode user to have access to the database (?). Therfore change the directory to this file and open it  

.. code-block:: console

	$ cd /etc/postgresql/9.2/main
	$ sudo vi pg_hba.conf

The file should contain the following default settings until now:

.. figure:: img/pg_hba_detail.png

and then set the authentication method of the following entry from *peer* to *trust*::

	#TYPE   DATABASE	USER	METHOD
	local	all		all	md5

After changing this file, the postgres service has to be restarted. This is essential, because otherwise the changed configurations won't be considered!

To restart the postgresql server type

.. code-block:: console

	$ sudo service postgresql restart


Additional entry::
	
	#Type	DATABASE	USER	ADDRESS		METHOD
	host	geonode		geonode	127.0.0.1/32	md5
	
Setup local settings
********************

The next step is to set the local settings. In the directory ../geonode/geonode a file called *local_settings.py.sample* exists. It includes all the settings to change the default db from *sqlite3* to *postgresql*. Rename the file to *local_settings.py*.

.. code-block:: console

	$ sudo mv local_settings.py.sample local_settings.py
	
Add::

	'PORT': '5432',
	
to your db settings in local_settings.py.

.. note:: If you do not use *geonode* as password for your database, then you have to edit the local_settings.py and change your password in this part of the file

.. figure:: img/local_settings_changes.PNG

Install psycopg2
****************

If you do not already have it on your machine, it is neccessary to install *psycopg2*, the postgresql adapter for Python programming language. But, be sure that you are working in your virtualenv, otherwise you will create a permission problem!! Thus activate your virtualenv first

.. code-block:: console

	$ source home/user/.venvs/geonode/bin/activate
	$ cd
	$ pip install psycopg2

Synchronise db
**************

To synchronise the database call the django command *syncdb*

.. code-block:: console

   $ django-admin.py syncdb --noinput --all
   

Create new superuser
********************

Furthermore a new django superuser has to be created

.. code-block:: console

   $ django-admin.py createsuperuser --settings=geonode.settings

You will be asked to enter a username, an email adress and a password.


Other steps
-----------

Create local static files
*************************

The collectstatic command will create a new folder *static_root*.

.. code-block:: console

   $ django-admin.py collectstatic --settings=geonode.settings --noinput

Enable geonode upload function
******************************

An empty folder called *uploaded* must be created

.. code-block:: console

   $ sudo mkdir -p /home/user/geonode/geonode/uploaded
   
When using apache webserver change owner to www-data

.. code-block:: console
   
   $ sudo chown www-data -R /home/user/geonode/geonode/uploaded
   
Replace local server with apache
--------------------------------

To replace the local server with apache2, you have to first make apache to load the mod_wsgi module. If you've done the installation from above, you should already have a *httpd.conf* file that includes one line

.. code-block:: python

  LoadModule wsgi_module /path/to/modules/mod_wsgi.so

If you do not have this, then please add this line to *httpd.conf* now!

Beside this module you also have to enable the proxy module. This can be done very easily using

.. code-block:: console

	$ sudo a2enmod proxy_http

We have to create one more configuration file for geonode. Go to the folder *sites-available* and create a file called *geonode*

.. code-block:: console

	$ cd /etc/apache2/sites-available
	$ sudo gedit geonode

This file should inlcude the following, but don´t forget to adjust the paths!

.. code-block:: python

  WSGIDaemonProcess geonode python-path=/home/barbara/geonode:/home/barbara/.venvs/geonode/lib/python2.7/site-packages user=www-data threads=15 processes=2

  <VirtualHost *:80>
	ServerName http://localhost:8000
	ServerAdmin webmaster@localhost
	DocumentRoot /home/barbara/geonode/geonode

	ErrorLog /var/log/apache2/error.log
	LogLevel warn
	CustomLog /var/log/apache2/access.log combined

	WSGIProcessGroup geonode
	WSGIPassAuthorization On
	WSGIScriptAlias / /home/barbara/geonode/geonode/wsgi.py

	<Directory "/home/barbara/geonode/geonode/">
		Order allow,deny
		Options Indexes FollowSymLinks
		Allow from all
		IndexOptions FancyIndexing
	</Directory>

	Alias /static/ /home/barbara/geonode/geonode/static/
	Alias /uploaded/ /home/barbara/geonode/geonode/uploaded/

	<Proxy *>
  		Order allow,deny
  		Allow from all
	</Proxy>

	ProxyPreserveHost On
	ProxyPass /geoserver http://localhost:8080/geoserver
	ProxyPassReverse /geoserver http://localhost:8080/geoserver
	ProxyPass /geonetwork http://localhost:8080/geonetwork
	ProxyPassReverse /geonetwork http://localhost:8080/geonetwork

  </VirtualHost>

Enable the new site

.. code-block:: console

	$ sudo a2ensite geonode

This command will create a file *geonode* in the folder *sites-enabled*.

Now reload apache

.. code-block:: console

	$ sudo service apache2 reload

If you now type localhost into your webbrowser, the geonode webpage will appear. You can now login with your newly created superuser account. But if you try to attend the django admin interface, you will only see the content of this webpage but without any design. To change this, you have to change the following entry in our geonode configuration file

.. code-block:: console

	$ sudo gedit /etc/apache2/sites-available/geonode

Change this entry::

	Alias /static/ /home/barbara/geonode/geonode/static/
	
to::

	Alias /static/ /home/barbara/geonode/geonode/static_root/

Now reload apache2 again using ``sudo service apache2 reload`` and visit localhost/admin. Now you should be able to see this

.. figure:: img/admin_interface.PNG

Replace default jetty server with tomcat - deploy geoserver
-----------------------------------------------------------

Until now you won't be able to attend the geoserver webpage (without using ``paver start_geoserver``). So we now want to deploy our own geoserver. To do so we need Tomcat installed and not running. So if you've got Tomcat running at the moment, stop it using

.. code-block:: console

	$ cd /opt/apache-tomcat-X.Y.Z/bin
	$ sudo ./shutdown.sh
	
When installing geonode in developing mode, you´ve also got a *geoserver.war* file included. You will find this in your geonode directory::

	geonode/downloaded/geoserver.war

Now copy this file into the *webapps* folder of tomcat

.. code-block:: console

	$ sudo cp geoserver.war /opt/apache-tomcat-7.0.42/webapps
	
By starting tomcat it will unpack the geoserver.war and create a new directory ``tomcat/webapps/geoserver``. 

.. code-block:: console

	$ cd /opt/apache-tomcat-X.Y.Z/bin
	$ sudo ./catalina.sh run
	$ sudo service apache2 reload
	
Let´s try to attend http://localhost:8080/geoserver or localhost/geoserver. You will now see the geoserver homepage.

.. figure:: img/geoserver_webpage.PNG

Change permissions of folders
-----------------------------

.. code-block:: console

   $ sudo chown www-data:www-data /home/user/geonode/geonode/static/
   $ sudo chown www-data:www-data /home/user/geonode/geonode/uploaded/
   $ sudo chown www-data:www-data /home/barbara/geonode/geonode/static_root/
   
   $ sudo service apache2 reload
   
   
