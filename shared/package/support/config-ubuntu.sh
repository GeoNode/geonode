# Location of the expanded GeoNode tarball
INSTALL_DIR=.
# Location of the target filesystem, it may be blank
# or something like $(CURDIR)/debian/geonode/
TARGET_ROOT=''
# Tomcat webapps directory
TOMCAT_WEBAPPS=$ROOT/var/lib/tomcat6/webapps
# Geoserver data dir, it will survive removals and upgrades
GEOSERVER_DATA_DIR=$ROOT/var/lib/geoserver/data
# Place where GeoNode media is going to be served
GEONODE_WWW=$ROOT/var/www/geonode
# Apache sites directory
APACHE_SITES=$ROOT/etc/apache2/sites-available
# Place where the GeoNode virtualenv would be installed
GEONODE_LIB=$ROOT/var/lib/geonode
# Path to preferred location of binaries (might be /usr/sbin for CentOS)
GEONODE_BIN=$ROOT/usr/bin/
# Path to place miscelaneous patches and scripts used during the install
GEONODE_SHARE=$ROOT/usr/share/geonode
# Path to GeoNode configuration and customization
GEONODE_ETC=$ROOT/etc/geonode
# Path to GeoNode logging folder
GEONODE_LOG=$ROOT/var/log/geonode
# OS preferred way of starting or stopping services
# for example 'service httpd' or '/etc/init.d/apache2'
APACHE_SERVICE="invoke-rc.d apache2"
# sama sama
TOMCAT_SERVICE="invoke-rc.d tomcat6"
