#!/bin/bash

# GeoNode installation file, this only copies the files in the right folder
source $1
#
# First step is to unpack the wars in the tomcat webapps dir
#
mkdir -p $TOMCAT_WEBAPPS/geoserver
mkdir -p $TOMCAT_WEBAPPS/geonetwork
unzip $HERE/geoserver.war -d $TOMCAT_WEBAPPS/geoserver
unzip $HERE/geonetwork.war -d $TOMCAT_WEBAPPS/geonetwork
# GeoServer data is better placed outside tomcat to survive reinstalls
mkdir -p $GEOSERVER_DATA_DIR
cp -rp $TOMCAT_WEBAPPS/geoserver/data/* $GEOSERVER_DATA_DIR
#
# Second step is to put the apache wsgi and conf files in the right places
#
mkdir -p $GEONODE_WWW/static
mkdir -p $GEONODE_WWW/uploaded
# The wsgi directory is where the Python / Django application is configured
mkdir -p $GEONODE_WWW/wsgi
cp -rp $HERE/support/geonode.wsgi $GEONODE_WWW/wsgi/
# The robots.txt file tells google and other crawlers not to harvest /geoserver
# or /geonetwork, asking for all the layers at the same time is too taxing.
cp -rp $HERE/support/geonode.robots $GEONODE_WWW/robots.txt
# The apache configuration has a placeholder for the final location of the
# geonode virtualenv, it should be the site-packages directory of the venv.
mkdir -p $APACHE_SITES
cp -rp $HERE/support/geonode.apache $APACHE_SITES/geonode
#
# Third step is to unpack the pybundle and put the virtualenv in the right place
#
mkdir -p $GEONODE_LIB
cp -rp $HERE/pavement.py $GEONODE_LIB
cp -rp $HERE/bootstrap.py $GEONODE_LIB
cp -rp $HERE/geonode-webapp.pybundle $GEONODE_LIB
# Fourth step is to install the binary
mkdir -p $GEONODE_BIN
cp -rp $HERE/support/geonode.binary $GEONODE_BIN/geonode
# Fifth step is to copy the scripts and patches that would be used in postinst	
mkdir -p $GEONODE_ETC
mkdir -p $GEONODE_ETC/geonetwork
mkdir -p $GEONODE_ETC/geoserver
# A copy of web.xml and config.xml are put with the config files
# they will be patched during the post-install and need to survive upgrades.
cp -rp $TOMCAT_WEBAPPS/geoserver/WEB-INF/web.xml $GEONODE_ETC/geoserver/
cp -rp $TOMCAT_WEBAPPS/geonetwork/WEB-INF/config.xml $GEONODE_ETC/geonetwork/
mkdir -p $GEONODE_SHARE
# This Django fixture contains a superuser called geonode that does not have
# a working password. It is used as the default superuser.
cp -rp $HERE/support/geonode.admin $GEONODE_SHARE/admin.json
cp -rp $HERE/support/geoserver.patch $GEONODE_SHARE
cp -rp $HERE/support/geonetwork.patch $GEONODE_SHARE
cp -rp $HERE/support/create_geonode_postgis.sh $GEONODE_SHARE
#
# Sixth step is to configure /etc/geonode/ with folders for custom media and templates
#
cp -rp $HERE/support/geonode.local_settings $GEONODE_ETC/local_settings.py
# Extra media put in the following directory will be collected in /var/www/geonode/static
# when 'geonode collectstatic -v0' is run.
mkdir -p $GEONODE_ETC/media
# The recommended way to change a template is to copy it from the original location into
# this directory, this one has precedence over all the other template locations.
mkdir -p $GEONODE_ETC/templates
