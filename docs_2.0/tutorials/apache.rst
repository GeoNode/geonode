Update Apache Configuration
=====================================

.. todo:: Add more text here!

Install Apache2
--------------------

First of all Apache2 has to be installed. This is very easy using the apt-get command in Ubuntu.

.. code-block:: console

	$ sudo apt-get install apache2

Install mod_wsgi
---------------------

Furthermore the Apache module *mod_wsgi* has to be installed. To do so go to http://code.google.com/p/modwsgi/downloads/list and download a source code tar ball.

Next, unpack it:

.. code-block:: console

	$ tar xvfz mod_wsgi-X.Y.tar.gz

(replace X.Y with the actual version number!)

To install the mod_wsgi module you will need a apache2 dev version as well, so if you do not have one, please type

.. code-block:: console

	$ sudo apt-get install apache2-dev

If apache2-dev has successfully be installed you can go further to install mod_wsgi from source:

.. code-block:: console

	$ cd mod_wsgi-X.Y
	$ ./configure
	$ make
	$ sudo make install

Now we have to load this module in apache2. To do so, open the *httpd.conf* file

.. code-block:: console

	$ sudo gedit /etc/apche2/httpd.conf

and add the following line::

	LoadModule wsgi_module /path/to/modules/mod_wsgi.so

.. note:: Be aware where *mod_wsgi.so* is located! It might be /usr/lib/apache2/modules/mod_wsgi.so but could also be somewhere else, depending on your system and version!

After this configuration apache2 has to be reloaded so that the configuration will be considered

.. code-block:: console

	$ sudo service apache2 reload

go back to mod_wsgi folder and run

.. code-block:: console

	$ make clean

To check whether you´ve successfully installed and added mod_wgsi go to ``var/log/apache2`` and open the log file. You should see a line like this::

	mod_wsgi/3.4 Python/2.7.3 configured -- resuming normal operations

Configure Apache2 
-----------------

In *httpd.conf* should only be one line, like explained above. This just makes apache to load the mod_wsgi module.

.. code-block:: python

  LoadModule wsgi_module /path/to/modules/mod_wsgi.so
  
Beside this module you also have to enable the proxy module. This can be done very easily using

.. code-block:: console

	$ a2enmod proxy proxy_http
	
.. todo:: I am not sure, which one has to be used!

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
	Alias /uploaded/ /home/barbara/geonode/geonode/geonode/uploaded/

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

	$sudo a2ensite geonode

This command will create a file *geonode* in the folder *sites-enabled*.

Now reload apache

.. code-block:: console

	$sudo service apache2 reload

If you now type localhost into your webbrowser, the geonode webpage will appear.


El final
--------

#. Start apache2 using

.. code-block:: console

	$ sudo service apache2 start
	
#. Start tomcat

.. code-block:: console

	$ /opt/apache-tomcat-7.0.42/bin
	$ sudo ./catalina.sh run

Set www-data as owner to the folders *uploaded* (this might have to be created first) and *static*.

Run the commands

.. code-block:: console

	$ django-admin.py collectstatic --noinput --settings=geonode.settings
	$ django-admin.py updatelayers --settings=geonode.settings --ignore-errors

The first one will create the folder *static_root* and the second one will update all layers from geoserver to geonode.

After you´ve run apache2 once with the geonode config file, change the following entry::

	Alias /static/ /home/user/geonode/geonode/static/
	
to::
	
	Alias /static/ /home/user/geonode/geonode/static_root/
	
.. hint:: you have to first dissable the site using ``a2dissite`` geonode, reload apache ``sudo service apache2 reload``, change the entry and the enable the site again and reload apache2.
