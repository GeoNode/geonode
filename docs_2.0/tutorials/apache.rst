Apache Installation and Configuration
=====================================

Geonode and apache2
===================

Installation apache2
--------------------

To install apache2 type

.. code-block:: console

$ sudo apt-get install apache2

Installation mod_wsgi
---------------------

Then the Apache2 module mod_wsgi has to be installed. To do so go to http://code.google.com/p/modwsgi/downloads/list and dwonload source code tar balls.

Unpack it with the command:

.. code-block:: console

$ tar xvfz mod_wsgi-X.Y.tar.gz

(replace X.Y with the actual version number!)

To install the mod_wsgi module you will need a apache2 dev version as well, so type::

.. code-block:: console

$ sudo apt-get install apache2-dev

This will download and install you *apache2-threaded-dev*. As a next step is to configure the source code:

.. code-block:: console

$ cd mod_wsgi-X.Y
$ ./configure
$ make
$ sudo make install



Now the module has to be loaded into apache2. To do so, add the following line into the *httpd.conf* file (you should find this in /apache2)::

 LoadModule wsgi_module modules/mod_wsgi.so

OBS: be aware where mod_wsgi.so is located!
in my case it was: /home/barbara/mod-wsgi-3.4/.lib/mod_wsgi.so

therefore enter
LoadModule wsgi_module modules/mod_wsgi.so

then you have to restart apache2

$ sudo service apache2 restart

go back to mod_wsgi folder and run

$ make clean

this should stand in your error log file (var/log/apache2):

mod_wsgi/3.4 Python/2.7.3 configured -- resuming normal operations


how to use django with apache and modwsgi
-----------------------------------------

.# basic config

   first edit the httpd.conf file; edit the following:

WSGIScriptAlias / /path/to/mysite.com/mysite/wsgi.py
WSGIPythonPath /path/to/mysite.com

<Directory /path/to/mysite.com/mysite>
<Files wsgi.py>
Order deny,allow
Allow from all
</Files>
</Directory>

for mit it looks like this

LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so

# change the owner of folder uploaded
chown -R www-data:www-data /usr/lib/python2.7/dist-packages/geonode/uploaded

# Collect static files
django-admin.py collectstatic --noinput --settings=geonode.settings

django-admin.py updatelayers --settings=geonode.settings --ignore-errors

# Make the apache user the owner of the required dirs.
chown www-data /usr/lib/python2.7/dist-packages/geonode/static/
chown www-data /usr/lib/python2.7/dist-packages/geonode/uploaded/

#Enable GeoNode and reload apache
a2ensite geonode => that didn't work, because forgot to create *geonode* in /etc/apache2/sites-available

# change apache entry to static_root
sed -i -e 's|Alias /static/ /usr/lib/python2.7/dist-packages/geonode/static|Alias /static/ /usr/lib/python2.7/dist-packages/geonode/static_root|' \
    /etc/apache2/sites-available/geonode

=> i did that manually; just changed it in /etc/apache2/sites-available/geonode 

# Reload Apache
/etc/init.d/apache2 force-reload

This is how it worked!

set www-data as owner to:
-uploaded
-static

run commands:
# Collect static files
django-admin.py collectstatic --noinput --settings=geonode.settings

django-admin.py updatelayers --settings=geonode.settings --ignore-errors


in httpd.conf is only one line

LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so


with this geonode file (sites-available) it worked!!!!!!

WSGIDaemonProcess geonode python-path=/home/barbara/geonode:/home/barbara/.venvs/geonode/lib/python2.7/site-packages user=www-data threads=15 processes=2


.. code-block:: python

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

	$sudo a2ensite geonde
	$sudo service apache2 restart

so now, when i type localhost into the machine, geonode appears!!!

change 

	Alias /static/ /home/barbara/geonode/geonode/static/
to
	Alias /static/ /home/barbara/geonode/geonode/static_root/

try to start geoserver
=> starting tomcat => works!!!

try updatelayers
=> permission denied!!

All together
------------

start apache2
	$ sudo service apache2 start
go to
	localhost
geonode will appear!

to attend the geoserver webpage, start tomcat
	$ /opt/apache-tomcat-7.0.42/bin
	$ ./catalina.sh run



