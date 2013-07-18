#!/bin/sh
# Copyright (c) 2013 Open Source Geospatial Foundation (OSGeo)
#
# Licensed under the GNU LGPL.
# 
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 2.1 of the License,
# or any later version.  This library is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY, without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details, either
# in the "LICENSE.LGPL.txt" file distributed with this software or at
# web page "http://www.fsf.org/licenses/lgpl.html".

# About:
# =====
# This script installs GeoNode.

# Running:
# =======
# sudo ./install_geonode.sh

SCRIPT="install_geonode.sh"
echo "==============================================================="
echo "$SCRIPT"
echo "==============================================================="

echo "Starting GeoNode installation"

if [ -z "$USER_NAME" ] ; then
    USER_NAME="user"
fi

USER_HOME="/home/$USER_NAME"
DATA_DIR="/usr/local/share/geonode"
DOC_DIR="$DATA_DIR/doc"
APACHE_CONF="/etc/apache2/sites-available/geonode"
POSTGRES_USER="$USER_NAME"
GEONODE_CONF="/etc/geonode/local_settings.py"

#Install packages
add-apt-repository -y ppa:geonode/unstable
apt-get -q update
apt-get --assume-yes install python-geonode libapache2-mod-wsgi

if [ $? -ne 0 ] ; then
    echo 'ERROR: Package install failed! Aborting.'
    exit 1
fi

# Add an entry in /etc/hosts for geonode, to enable http://geonode/
echo '127.0.0.1 geonode' | sudo tee -a /etc/hosts


# Deploy demonstration instance in Apache
echo "Deploying geonode demonstration instance"
cat << EOF > "$APACHE_CONF"
WSGIDaemonProcess geonode user=www-data threads=15 processes=2
<VirtualHost *:80>
    ServerName geonode
    ServerAdmin webmaster@localhost

    ErrorLog /var/log/apache2/error.log
    LogLevel warn
    CustomLog /var/log/apache2/access.log combined

    WSGIProcessGroup geonode
    WSGIPassAuthorization On
    WSGIScriptAlias / /usr/lib/python2.7/dist-packages/geonode/wsgi.py

    <Directory "/usr/lib/python2.7/disk-packages/geonode/">
       Order allow,deny
        Options Indexes FollowSymLinks
        Allow from all
        IndexOptions FancyIndexing
    </Directory>

    Alias /static/ /usr/lib/python2.7/dist-packages/geonode/static/
    Alias /uploaded/ /usr/lib/python2.7/dist-packages/geonode/uploaded/

    <Proxy *>
      Order allow,deny
      Allow from all
    </Proxy>

    ProxyPreserveHost On
    ProxyPass /geoserver http://localhost:8082/geoserver
    ProxyPassReverse /geoserver http://localhost:8082/geoserver
</VirtualHost>
EOF
echo "Done"


#FIXME: The default configuration in apache does not have a ServerName for localhost
# and takes over requests for GeoNode's virtualhost, the following patch is a workaround:
cat << EOF > "$TMP_DIR/servername.patch"
--- /etc/apache2/sites-available/default.ORIG	2013-07-17 19:29:32.559707270 +0000
+++ /etc/apache2/sites-available/default	2013-07-17 19:30:50.703705186 +0000
@@ -1,5 +1,7 @@
 <VirtualHost *:80>
 	ServerAdmin webmaster@localhost
+        ServerName localhost
+        ServerAlias osgeolive
 
 	DocumentRoot /var/www
 	<Directory />
EOF

if [ `grep -c 'ServerName' /etc/apache2/sites-available/default` -eq 0 ] ; then
  patch -p0 < "$TMP_DIR/servername.patch"
fi

# Create tables in the database
django-admin syncdb --all --noinput --settings=geonode.settings
# Install sample admin. Username:admin password:admin
django-admin loaddata sample_admin
# Collect static files
django-admin collectstatic --noinput --settings=geonode.settings


# Make the apache user the owner of the required dirs.
chown www-data /usr/lib/python2.7/dist-packages/geonode/development.db
chown www-data /usr/lib/python2.7/dist-packages/geonode/static/
chown www-data /usr/lib/python2.7/dist-packages/geonode/uploaded/


# Install desktop icon
echo "Installing geonode icon"
cp -f "$USER_HOME/gisvm/app-conf/geonode/geonode.png" \
       /usr/share/icons/

# Add Launch icon to desktop
if [ ! -e /usr/local/share/applications/geonode.desktop ] ; then
    cat << EOF > /usr/local/share/applications/geonode.desktop
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name=GeoNode
Comment=Starts GeoNode
Categories=Application;Geography;Geoscience;Education;
Exec=firefox http://localhost/geonode/
Icon=/usr/share/icons/geonode.png
Terminal=false
StartupNotify=false
EOF
fi

cp /usr/local/share/applications/geonode.desktop "$USER_HOME/Desktop/"
chown -R $USER_NAME.$USER_NAME "$USER_HOME/Desktop/geonode.desktop"


# geonode Documentation
echo "Getting geonode documentation"
[ -d "$DOC_DIR" ] || mkdir -p "$DOC_DIR"

cd "$DOC_DIR"
chmod g+w .
chgrp users .

wget -c --progress=dot:mega \
    "https://media.readthedocs.org/pdf/geonode/latest/geonode.pdf" \
    -O geonode_documentation-latest.pdf

ln -sf geonode_documentation-latest.pdf geonode_documentation.pdf
chmod g+w -R geonode_documentation*
chgrp users -R geonode_documentation*
ln -sTf "$DOC_DIR" /var/www/geonode-docs

# Add Documentation Launch icon to desktop
if [ ! -e /usr/local/share/applications/geonode-docs.desktop ] ; then
    cat << EOF > /usr/local/share/applications/geonode-docs.desktop
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name=GeoNode Documentation
Comment=GeoNode Documentation
Categories=Application;Geography;Geoscience;Education;
Exec=evince "$DOC_DIR/geonode_documentation.pdf"
Icon=/usr/share/icons/geonode.png
Terminal=false
StartupNotify=false
EOF
fi
cp -a /usr/local/share/applications/geonode-docs.desktop "$USER_HOME/Desktop/"
chown -R $USER_NAME:$USER_NAME "$USER_HOME/Desktop/geonode-docs.desktop"

#Enable GeoNode and reload apache
a2ensite geonode

# Reload Apache
/etc/init.d/apache2 force-reload

# Uninstall dev packages
apt-get --assume-yes autoremove

echo "==============================================================="
echo "Finished $SCRIPT"
echo Disk Usage1:, $SCRIPT, `df . -B 1M | grep "Filesystem" | sed -e "s/  */,/g"`, date
echo Disk Usage2:, $SCRIPT, `df . -B 1M | grep " /$" | sed -e "s/  */,/g"`, `date`
echo "==============================================================="
