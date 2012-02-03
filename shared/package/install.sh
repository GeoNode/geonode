#!/usr/bin/env bash
# GeoNode installer script
#
# using getopts
#

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

while getopts 's:' OPTION
do
  case $OPTION in
  s)	stepflag=1
		stepval="$OPTARG"
		;;
  ?)	printf "Usage: %s: [-s value] configfile\n" $(basename $0) >&2
		exit 2
		;;
  esac
done
shift $(($OPTIND - 1))


function preinstall() {
	# Places the geonode files in the right location in the file system

	#
	# First step is to unpack the wars in the tomcat webapps dir
	#
	mkdir -p $TOMCAT_WEBAPPS/geoserver
	mkdir -p $TOMCAT_WEBAPPS/geonetwork
	unzip -qq $INSTALL_DIR/geoserver.war -d $TOMCAT_WEBAPPS/geoserver
	unzip -qq $INSTALL_DIR/geonetwork.war -d $TOMCAT_WEBAPPS/geonetwork
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
	cp -rp $INSTALL_DIR/support/geonode.wsgi $GEONODE_WWW/wsgi/
	# The robots.txt file tells google and other crawlers not to harvest /geoserver
	# or /geonetwork, asking for all the layers at the same time is too taxing.
	cp -rp $INSTALL_DIR/support/geonode.robots $GEONODE_WWW/robots.txt
	# The apache configuration has a placeholder for the final location of the
	# geonode virtualenv, it should be the site-packages directory of the venv.
	mkdir -p $APACHE_SITES
	cp -rp $INSTALL_DIR/support/geonode.apache $APACHE_SITES/geonode
	#
	# Third step is to unpack the pybundle and put the virtualenv in the right place
	#
	mkdir -p $GEONODE_LIB
	cp -rp $INSTALL_DIR/geonode-webapp.pybundle $GEONODE_LIB
	# Fourth step is to install the binary
	mkdir -p $GEONODE_BIN
	cp -rp $INSTALL_DIR/support/geonode.binary $GEONODE_BIN/geonode
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
	cp -rp $INSTALL_DIR/support/geonode.admin $GEONODE_SHARE/admin.json
	cp -rp $INSTALL_DIR/support/geoserver.patch $GEONODE_SHARE
	cp -rp $INSTALL_DIR/support/geonetwork.patch $GEONODE_SHARE
	#
	# Sixth step is to configure /etc/geonode/ with folders for custom media and templates
	#
	cp -rp $INSTALL_DIR/support/geonode.local_settings $GEONODE_ETC/local_settings.py
	# Extra media put in the following directory will be collected in /var/www/geonode/static
	# when 'geonode collectstatic -v0' is run.
	mkdir -p $GEONODE_ETC/media
	# The recommended way to change a template is to copy it from the original location into
	# this directory, this one has precedence over all the other template locations.
	mkdir -p $GEONODE_ETC/templates
}

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
	# Patch geoserver and geonetwork config files
	patch $GEONODE_ETC/geonetwork/config.xml $GEONODE_SHARE/geonetwork.patch
	patch $GEONODE_ETC/geoserver/web.xml $GEONODE_SHARE/geoserver.patch
	# Let geonetwork know the geonode password
	sed -i "s/GEONODE_DATABASE_PASSWORD/$psqlpass/g" $GEONODE_ETC/geonetwork/config.xml
	rm -rf $TOMCAT_WEBAPPS/geonetwork/WEB-INF/config.xml
	ln -sf $GEONODE_ETC/geonetwork/config.xml $TOMCAT_WEBAPPS/geonetwork/WEB-INF/config.xml
	rm -rf $TOMCAT_WEBAPPS/geoserver/WEB-INF/web.xml
	cp -rp $GEONODE_ETC/geoserver/web.xml $TOMCAT_WEBAPPS/geoserver/WEB-INF/web.xml
	# Set up logging symlinks to /var/log/geonode
	mkdir -p $GEONODE_LOG
	ln -sf /var/log/tomcat6/catalina.out $GEONODE_LOG/tomcat.log
	ln -sf /var/log/tomcat6/geonetwork.log $GEONODE_LOG/geonetwork.log
	ln -sf $GEOSERVER_DATA_DIR/logs/geoserver.log $GEONODE_LOG/geoserver.log

        # Set the tomcat user as the owner
        chown tomcat6. $GEOSERVER_DATA_DIR -R
        chown tomcat6. $TOMCAT_WEBAPPS/geonetwork -R
        chown tomcat6. $TOMCAT_WEBAPPS/geoserver -R

	$TOMCAT_SERVICE restart
}

function configurepostgres() {
	# configure postgres user and database
	#

	psqlpass=$(randpass 8 0)
        if su - postgres -c 'psql -l | grep -q geonode'
        then
	    echo
	else
	    su - postgres -c "createdb -E UTF8 geonode"
	    su - postgres -c "createlang -d geonode plpgsql"
	    su - postgres -c "psql -d geonode -f $POSTGIS_SQL_PATH/$POSTGIS_SQL"
	    su - postgres -c "psql -d geonode -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql"
	    su - postgres -c "psql -d geonode -c 'GRANT ALL ON geometry_columns TO PUBLIC;'"
	    su - postgres -c "psql -d geonode -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'"

	    if ((GEOGRAPHY))
	    then
	        su - postgres -c "psql -d geonode -c 'GRANT ALL ON geography_columns TO PUBLIC;'"
	    fi
	    echo "CREATE ROLE geonode with login password '$psqlpass' SUPERUSER INHERIT;" >> $GEONODE_SHARE/role.sql
	    su - postgres -c "psql < $GEONODE_SHARE/role.sql"
	fi
}

function configuredjango() {
	# set up django
	#
	cd $GEONODE_LIB

	# Install the latest version of pip and virtualenv from PyPi to avoid having
        # problems in Ubuntu 10.04
	# FIXME: It is less than ideal that this command access the network. Ideas?
	easy_install -U virtualenv
	easy_install -U pip

	virtualenv .

	# Verify if the virtualenv has been created and abort if bin/activate does not exist
	if [ ! -f bin/activate ]
	then
	    echo "Creation of virtualenv failed, aborting installation"
	    exit -1
	fi

	source bin/activate
	touch geoserver_token
	pip install geonode-webapp.pybundle

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

	ln -sf $GEONODE_ETC/local_settings.py $GEONODE_LIB/src/GeoNodePy/geonode/local_settings.py
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
	$APACHE_SERVICE restart
}

function postinstall {
	configurepostgres
	configuretomcat
	configuredjango
	configureapache
}

if [ $# -eq 1 ]
then
	printf "Sourcing %s as the configuration file\n" $1
	source $1
else
 	printf "Usage: %s: [-s value] configfile\n" $(basename $0) >&2
        exit 2
fi

if [ "$stepflag" ]
then
	printf "\tStep: '$stepval specified\n"
else
	stepval="all"
	echo "heh"
fi

case $stepval in                                                                                                 
	pre)
		echo "Running GeoNode preinstall ..."
		preinstall
		;;
	post)
		echo "Running GeoNode postinstall ..."
		postinstall
		;;
	all)
		echo "Running GeoNode installation ..."
		preinstall
		postinstall
		;;
	*)
	        printf "\tValid values for step parameter are: 'pre', 'post','all'\n"
		printf "\tDefault value for step is 'all'\n"
		;;
esac
