#!/bin/bash

# Location of the expanded GeoNode tarball
INSTALL_DIR=.
# Location of the target filesystem, it may be blank
# or something like $(CURDIR)/debian/geonode/
TARGET_ROOT=''
# Tomcat webapps directory
TOMCAT_WEBAPPS=$TARGET_ROOT/var/lib/tomcat6/webapps
# Geoserver data dir, it will survive removals and upgrades
GEOSERVER_DATA_DIR=$TARGET_ROOT/var/lib/geoserver/geonode-data
# Place where GeoNode media is going to be served
GEONODE_WWW=$TARGET_ROOT/var/www/geonode
# Apache sites directory
APACHE_SITES=$TARGET_ROOT/etc/apache2/sites-available
# Place where the GeoNode virtualenv would be installed
GEONODE_LIB=$TARGET_ROOT/var/lib/geonode
# Path to preferred location of binaries (might be /usr/sbin for CentOS)
GEONODE_BIN=$TARGET_ROOT/usr/bin/
# Path to place miscelaneous patches and scripts used during the install
GEONODE_SHARE=$TARGET_ROOT/usr/share/geonode
# Path to GeoNode configuration and customization
GEONODE_ETC=$TARGET_ROOT/etc/geonode
# Path to GeoNode logging folder
GEONODE_LOG=$TARGET_ROOT/var/log/geonode
# OS preferred way of starting or stopping services
# for example 'service httpd' or '/etc/init.d/apache2'
APACHE_SERVICE="invoke-rc.d apache2"
# sama sama
TOMCAT_SERVICE="invoke-rc.d tomcat6"

# For Ubuntu 10.04
if [ -d "/usr/share/postgresql/8.4/contrib" ]
then
    POSTGIS_SQL_PATH=/usr/share/postgresql/8.4/contrib
    POSTGIS_SQL=postgis.sql
fi

# For Ubuntu 10.10 (with PostGIS 1.5)
if [ -d "/usr/share/postgresql/8.4/contrib/postgis-1.5" ]
then
    POSTGIS_SQL_PATH=/usr/share/postgresql/8.4/contrib/postgis-1.5
    POSTGIS_SQL=postgis.sql
    GEOGRAPHY=1
else
    GEOGRAPHY=0
fi

# For Ubuntu 12.04 (with PostGIS 1.5)
if [ -d "/usr/share/postgresql/9.1/contrib/postgis-1.5" ]
then
    POSTGIS_SQL_PATH=/usr/share/postgresql/9.1/contrib/postgis-1.5
    POSTGIS_SQL=postgis.sql
    GEOGRAPHY=1
else
    GEOGRAPHY=0
fi