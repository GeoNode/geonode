.. _setup_configure_httpd:

=======================
Setup & Configure HTTPD
=======================

In this section we are going to setup Apache HTTP to serve GeoNode.

Apache Configuration
====================

Navigate to Apache configurations folder:::

    cd /etc/apache2/sites-available

And create a new configuration file for GeoNode:::

    sudo gedit geonode.conf

Place the following content inside the file:::

    WSGIDaemonProcess geonode python-path=/home/geonode/geonode:/home/geonode/.venvs/geonode/lib/python2.7/site-packages user=www-data threads=15 processes=2

    <VirtualHost *:80>
        ServerName http://localhost
        ServerAdmin webmaster@localhost
        DocumentRoot /home/geonode/geonode/geonode

        ErrorLog /var/log/apache2/error.log
        LogLevel warn
        CustomLog /var/log/apache2/access.log combined

        WSGIProcessGroup geonode
        WSGIPassAuthorization On
        WSGIScriptAlias / /home/geonode/geonode/geonode/wsgi.py

        Alias /static/ /home/geonode/geonode/geonode/static_root/
        Alias /uploaded/ /home/geonode/geonode/geonode/uploaded/

        <Directory "/home/geonode/geonode/geonode/">
             <Files wsgi.py>
                 Order deny,allow
                 Allow from all
                 Require all granted
             </Files>

            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/geonode/geonode/static_root/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/geonode/geonode/uploaded/thumbs/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Directory "/home/geonode/geonode/geonode/uploaded/layers/">
            Order allow,deny
            Options Indexes FollowSymLinks
            Allow from all
            Require all granted
            IndexOptions FancyIndexing
        </Directory>

        <Proxy *>
            Order allow,deny
            Allow from all
        </Proxy>

        ProxyPreserveHost On
        ProxyPass /geoserver http://127.0.0.1:8080/geoserver
        ProxyPassReverse /geoserver http://127.0.0.1:8080/geoserver

    </VirtualHost>

This sets up a VirtualHost in Apache HTTP server for GeoNode and a reverse proxy
for GeoServer.

.. note::

    In the case that GeoServer is running on a separate machine change the `ProxyPass`
    and `ProxyPassReverse` accordingly

Now load apache `poxy` module::

    sudo a2enmod proxy_http

And enable geonode configuration file::

    sudo a2ensite geonode

Dowload GeoNode data to be served by Apache. You will be prompted for confirmation::

    cd /home/geonode/geonode/
    sudo -u geonode python manage.py collectstatic

Add `thumbs` and `layers` folders::

    sudo mkdir -p /home/geonode/geonode/geonode/uploaded/thumbs
    sudo mkdir -p /home/geonode/geonode/geonode/uploaded/layers

Change permissions on GeoNode files and folders to allow Apache to read and edit
them:::

    sudo chown -R geonode /home/geonode/geonode/
    sudo chown geonode:www-data /home/geonode/geonode/geonode/static/
    sudo chown geonode:www-data /home/geonode/geonode/geonode/uploaded/
    chmod -Rf 777 /home/geonode/geonode/geonode/uploaded/thumbs
    chmod -Rf 777 /home/geonode/geonode/geonode/uploaded/layers
    sudo chown www-data:www-data /home/geonode/geonode/geonode/static_root/

Finally restart Apache to load the new configuration::

    sudo service apache2 restart
