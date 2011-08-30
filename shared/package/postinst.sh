#!/bin/bash
# postinst script for geonode

set -e

TOMCAT_WEBAPPS=/var/lib/tomcat6/webapps
GEOSERVER_DATA_DIR=/var/lib/geoserver/data
GEONODE_WWW=/var/www/geonode
APACHE_SITES=/etc/apache2/sites-available
GEONODE_LIB=/var/lib/geonode
GEONODE_BIN=/usr/bin/
GEONODE_SHARE=/usr/share/geonode
GEONODE_ETC=/etc/geonode
GEONODE_LOG=/var/log/geonode


function randpass() {
  [ "$2" == "0" ] && CHAR="[:alnum:]" || CHAR="[:graph:]"
    cat /dev/urandom | tr -cd "$CHAR" | head -c ${1:-32}
    echo
}

function configuretomcat() {

	# configure tomcat defaults to avoid geonetwork bug and increase the available ram
	if grep saxon /etc/default/tomcat6
	then
		echo
	else
		cat <<- EOF >> /etc/default/tomcat6
		JAVA_OPTS='-Djava.awt.headless=true -Xmx1024m -Xms1024M -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement'
		EOF
	fi
	# Let geonetwork know the geonode password
	sed -i "s/GEONODE_DATABASE_PASSWORD/$psqlpass/g" $GEONODE_ETC/geonetwork/config.xml
	rm -rf $TOMCAT_WEBAPPS/geonetwork/WEB-INF/config.xml
	ln -sf $GEONODE_ETC/geonetwork/config.xml $TOMCAT_WEBAPPS/geonetwork/WEB-INF/config.xml
	rm -rf $TOMCAT_WEBAPPS/geoserver/WEB-INF/web.xml
	cp -rp $GEONODE_ETC/geoserver/web.xml $TOMCAT_WEBAPPS/geoserver/WEB-INF/web.xml
	# Set up logging symlinks to /var/log/geonode
	mkdir -p $GEONODE_LOG
	ln -sf /var/logs/tomcat6/catalina.out $GEONODE_LOG/tomcat.log
	ln -sf /var/logs/tomcat6/geonetwork.log $GEONODE_LOG/geonetwork.log
	ln -sf $GEOSERVER_DATA_DIR/logs/geoserver.log $GEONODE_LOG/geoserver.log

        # Set the tomcat user as the owner
        chown tomcat6. $GEOSERVER_DATA_DIR -R
        chown tomcat6. $TOMCAT_WEBAPPS/geonetwork -R
        chown tomcat6. $TOMCAT_WEBAPPS/geoserver -R

	invoke-rc.d tomcat6 restart
}

function configurepostgres() {
	# configure postgres user and database
	#
        if su - postgres -c 'psql -l | grep -q template_postgis'
        then
	    echo "Postgis template database found, using that one as template for geonode"
	else
	    su - postgres $GEONODE_SHARE/create_template_postgis-debian.sh
	fi

	psqlpass=$(randpass 8 0)
        if su - postgres -c 'psql -l | grep -q geonode'
        then
	    echo
	else
	    su - postgres -c "createdb geonode -T template_postgis"
	    echo "CREATE ROLE geonode with login password '$psqlpass' SUPERUSER INHERIT;" > /usr/share/geonode/role.sql
	    su - postgres -c "psql < $GEONODE_SHARE/role.sql"
	fi
}

function configuredjango() {
	# set up django
	#
	cd $GEONODE_LIB
	python bootstrap.py

	if [ -d src/GeoNodePy/geonode/media/static ]
	then
            mv -f src/GeoNodePy/geonode/media/static src/GeoNodePy/geonode/media/geonode
	fi

	if grep THE_SECRET_KEY $GEONODE_ETC/local_settings.py
	then
	    secretkey=$(randpass 18 0)
	    geoserverpass=$(randpass 8 0)

	    sed -i "s/THE_SECRET_KEY/$secretkey/g" $GEONODE_ETC/local_settings.py
	    sed -i "s/THE_GEOSERVER_PASSWORD/$geoserverpass/g" $GEONODE_ETC/local_settings.py
	    sed -i "s/THE_DATABASE_PASSWORD/$psqlpass/g" $GEONODE_ETC/local_settings.py
	fi

	ln -s $GEONODE_ETC/local_settings.py $GEONODE_LIB/src/GeoNodePy/geonode/local_settings.py
	# Set up logging symlink
	ln -sf /var/log/apache2/error.log $GEONODE_LOG/apache.log

	chmod +x $GEONODE_BIN/geonode
	geonode syncdb --noinput
	geonode collectstatic -v0 --noinput
	geonode loaddata /usr/share/geonode/admin.json
}

function configureapache() {
	# Setup apache
	#
	chown www-data -R $GEONODE_WWW
	a2dissite default
	a2enmod proxy_http
	sitedir=`$GEONODE_LIB/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`
        
	sed -i '1d' $APACHE_SITES/geonode
	sed -i "1i WSGIDaemonProcess geonode user=www-data threads=15 processes=2 python-path=$sitedir" $APACHE_SITES/geonode

	a2ensite geonode
	invoke-rc.d apache2 restart
}

configurepostgres
configuretomcat
configuredjango
configureapache
