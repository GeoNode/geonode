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


#Install packages
apt-get -q update
apt-get --assume-yes install gcc libgdal1-dev python-gdal libxml2 python-lxml \
    python-libxml2 python-pip libproj0 libproj-dev libgeos-dev libgeos++-dev \
    libapache2-mod-wsgi python-shapely python-pycsw python-owslib libxml2-dev libxslt-dev python-dev

if [ $? -ne 0 ] ; then
    echo 'ERROR: Package install failed! Aborting.'
    exit 1
fi


# Install geonode
pip install --upgrade geonode==2.0b10


# Create database for demonstration instance
sudo -u $POSTGRES_USER createdb geonode
sudo -u $POSTGRES_USER psql geonode -c 'create extension postgis;'

# Initialize database
django-admin.py syncdb --noinput --settings=geonode.settings

# Collect static files
django-admin.py collectstatic --noinput --settings=geonode.settings


#### final tidy up
sudo -u "$POSTGRES_USER" psql geonode -c 'VACUUM ANALYZE;'


# Deploy demonstration instance in Apache
echo "Deploying geonode demonstration instance"
cat << EOF > "$APACHE_CONF"
WSGIDaemonProcess geonode user=www-data threads=15 processes=2
<VirtualHost geonode:80>
    Servername geonode
    ServerAdmin webmaster@localhost

    ErrorLog /var/log/apache2/error.log
    LogLevel warn
    CustomLog /var/log/apache2/access.log combined

    WSGIProcessGroup geonode
    WSGIPassAuthorization On
    WSGIScriptAlias / /usr/local/lib/python2.7/disk-packages/geonode/wsgi.py

    <Directory "/usr/local/lib/python2.7/disk-packages/geonode/">
       Order allow,deny
        Options Indexes FollowSymLinks
        Allow from all
        IndexOptions FancyIndexing
    </Directory>

    Alias /static/ /usr/local/lib/python2.7/disk-packages/geonode/static/
    Alias /uploaded/ /usr/local/lib/python2.7/disk-packages/geonode/uploaded/

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


# Install desktop icon
echo "Installing geonode icon"
if [ ! -e "/usr/share/icons/geonode_60x60.logo.png" ] ; then
    wget -c --progress=dot:mega \
        "http://geonode.org/logo-geonode-livedvd.png" \
        -O /usr/share/icons/geonode_60x60.logo.png
fi


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
Icon=/usr/share/icons/geonode_60x60.logo.png
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
    "http://https://media.readthedocs.org/pdf/geonode/latest/geonode.pdf" \
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
Icon=/usr/share/icons/geonode_60x60.logo.png
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

echo "geonode 127.0.0.1" >> /etc/hosts

# Uninstall dev packages
apt-get --assume-yes remove libgdal1-dev libproj-dev libgeos-dev libgeos++-dev libxml2-dev libxslt-dev python-dev
apt-get --assume-yes autoremove

echo "==============================================================="
echo "Finished $SCRIPT"
echo Disk Usage1:, $SCRIPT, `df -B 1M | grep "Filesystem" | sed -e "s/  */,/g"`, date
echo Disk Usage2:, $SCRIPT, `df -B 1M | grep " /$" | sed -e "s/  */,/g"`, `date`
echo "==============================================================="
