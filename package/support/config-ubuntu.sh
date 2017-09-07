#!/bin/bash

# Location of the GeoNode source
INSTALL_DIR=.
# Location of the target directory, it may be blank
# or something like $(CURDIR)/debian/geonode/
TARGET_ROOT=''
# Tomcat webapps directory
TOMCAT_WEBAPPS=$TARGET_ROOT/var/lib/tomcat8/webapps
# Geoserver data dir, it will survive removals and upgrades
GEOSERVER_DATA_DIR=$TARGET_ROOT/var/lib/geoserver/geonode-data
# Place where GeoNode media is going to be served
GEONODE_WWW=$TARGET_ROOT/var/www/geonode
# Apache sites directory
APACHE_SITES=$TARGET_ROOT/etc/apache2/sites-available
# Path to preferred location of binaries (might be /usr/sbin for CentOS)
GEONODE_BIN=$TARGET_ROOT/usr/sbin/
# Path to place miscellaneous patches and scripts used during the install
GEONODE_SHARE=$TARGET_ROOT/usr/share/geonode
# Path to GeoNode configuration and customization
GEONODE_ETC=$TARGET_ROOT/etc/geonode
# Path to GeoNode logging folder
GEONODE_LOG=$TARGET_ROOT/var/log/geonode
# OS preferred way of starting or stopping services
# for example 'service httpd' or '/etc/init.d/apache2'
APACHE_SERVICE="invoke-rc.d apache2"
# sama sama
TOMCAT_SERVICE="invoke-rc.d tomcat8"
