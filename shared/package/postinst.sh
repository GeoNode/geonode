#!/bin/bash
# postinst script for geonode

set -e

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
	sed -i "s/GEONODE_DATABASE_PASSWORD/$psqlpass/g" /etc/geonode/geonetwork/config.xml
	rm -rf /var/lib/tomcat6/webapps/geonetwork/WEB-INF/config.xml
	ln -sf /etc/geonode/geonetwork/config.xml /var/lib/tomcat6/webapps/geonetwork/WEB-INF/config.xml
	rm -rf /var/lib/tomcat6/webapps/geoserver/WEB-INF/web.xml
	cp -rp /etc/geonode/geoserver/web.xml /var/lib/tomcat6/webapps/geoserver/WEB-INF/web.xml
	# Set up logging symlinks to /var/log/geonode
	mkdir -p /var/log/geonode
	ln -sf /var/lib/tomcat6/logs/catalina.out /var/log/geonode/tomcat.log
	ln -sf /var/lib/tomcat6/logs/geonetwork.log /var/log/geonode/geonetwork.log
	ln -sf /var/lib/geoserver/data/logs/geoserver.log /var/log/geonode/geoserver.log

        # Set the tomcat user as the owner
        chown tomcat6. /var/lib/geoserver/data/ -R
        chown tomcat6. /var/lib/tomcat6/webapps/geonetwork -R
        chown tomcat6. /var/lib/tomcat6/webapps/geoserver -R

	invoke-rc.d tomcat6 restart
}

function configurepostgres() {
	# configure postgres user and database
	#
        if su - postgres -c 'psql -l | grep -q template_postgis'
        then
	    echo "Postgis template database found, using that one as template for geonode"
	else
	    su - postgres /usr/share/geonode/create_template_postgis-debian.sh
	fi

	psqlpass=$(randpass 8 0)
        if su - postgres -c 'psql -l | grep -q geonode'
        then
	    echo
	else
	    su - postgres -c "createdb geonode -T template_postgis"
	    echo "CREATE ROLE geonode with login password '$psqlpass' SUPERUSER INHERIT;" > /usr/share/geonode/role.sql
	    su - postgres -c "psql < /usr/share/geonode/role.sql"
	fi
}

function configuredjango() {
	# set up django
	#
	cd /var/lib/geonode
	python bootstrap.py

	if [ -d src/GeoNodePy/geonode/media/static ]
	then
            mv -f src/GeoNodePy/geonode/media/static src/GeoNodePy/geonode/media/geonode
	fi

	if grep THE_SECRET_KEY /etc/geonode/local_settings.py
	then
	    secretkey=$(randpass 18 0)
	    geoserverpass=$(randpass 8 0)

	    sed -i "s/THE_SECRET_KEY/$secretkey/g" /etc/geonode/local_settings.py
	    sed -i "s/THE_GEOSERVER_PASSWORD/$geoserverpass/g" /etc/geonode/local_settings.py
	    sed -i "s/THE_DATABASE_PASSWORD/$psqlpass/g" /etc/geonode/local_settings.py
	fi

	ln -s /etc/geonode/local_settings.py /var/lib/geonode/src/GeoNodePy/geonode/local_settings.py
	# Set up logging symlink
	ln -sf /var/log/apache2/error.log /var/log/geonode/apache.log

	chmod +x /usr/bin/geonode
	geonode syncdb --noinput
	geonode collectstatic -v0 --noinput
	geonode loaddata /usr/share/geonode/admin.json
}

function configureapache() {
	# Setup apache
	#
	chown www-data -R /var/www/geonode/
	a2dissite default
	a2enmod proxy_http
	sitedir=`/var/lib/geonode/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`
        
	sed -i '1d' /etc/apache2/sites-available/geonode
	sed -i "1i WSGIDaemonProcess geonode user=www-data threads=15 processes=2 python-path=$sitedir" /etc/apache2/sites-available/geonode

	a2ensite geonode
	invoke-rc.d apache2 restart
}

configurepostgres
configuretomcat
configuredjango
configureapache
