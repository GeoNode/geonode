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

function setup_directories() {
	mkdir -p $GEOSERVER_DATA_DIR
	mkdir -p $GEONODE_WWW/static
	mkdir -p $GEONODE_WWW/uploaded
	mkdir -p $GEONODE_WWW/wsgi
	mkdir -p $APACHE_SITES
	mkdir -p $GEONODE_LIB
	mkdir -p $GEONODE_BIN
	mkdir -p $GEONODE_ETC
	mkdir -p $GEONODE_ETC/media
	mkdir -p $GEONODE_ETC/templates
	mkdir -p $GEONODE_SHARE
}

function reorganize_configuration() {
	cp -rp $INSTALL_DIR/support/geonode.apache $APACHE_SITES/geonode
	cp -rp $INSTALL_DIR/support/geonode.wsgi $GEONODE_WWW/wsgi/
	cp -rp $INSTALL_DIR/support/geonode.robots $GEONODE_WWW/robots.txt
	cp -rp $INSTALL_DIR/GeoNode*.zip $GEONODE_LIB
	cp -rp $INSTALL_DIR/support/geonode.binary $GEONODE_BIN/geonode
	cp -rp $INSTALL_DIR/support/geonode.updateip $GEONODE_BIN/geonode-updateip
	cp -rp $INSTALL_DIR/support/geonode.admin $GEONODE_SHARE/admin.json
	cp -rp $INSTALL_DIR/support/geonode.local_settings $GEONODE_ETC/local_settings.py

	chmod +x $GEONODE_BIN/geonode
	chmod +x $GEONODE_BIN/geonode-updateip
}

function preinstall() {
    setup_directories
    reorganize_configuration
}

function randpass() {
  [ "$2" == "0" ] && CHAR="[:alnum:]" || CHAR="[:graph:]"
    cat /dev/urandom | tr -cd "$CHAR" | head -c ${1:-32}
    echo
}

function setup_postgres_once() {
    su - postgres <<EOF
createdb -E UTF8 geonode
createlang -d geonode plpgsql
psql -d geonode -f $POSTGIS_SQL_PATH/$POSTGIS_SQL
psql -d geonode -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
psql -d geonode -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
psql -d geonode -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
EOF
if ((GEOGRAPHY))
then
    su - postgres -c "psql -d geonode -c 'GRANT ALL ON geography_columns TO PUBLIC;'"
fi
su - postgres -c "psql" <<EOF
CREATE ROLE geonode WITH LOGIN PASSWORD '$psqlpass' SUPERUSER INHERIT;
EOF
}

function setup_postgres_every_time() {
    true # nothing to do. when we setup DB migrations they'll probably go here.
}

function setup_django_once() {
    sed -i "s/THE_SECRET_KEY/$secretkey/g" $GEONODE_ETC/local_settings.py
    sed -i "s/THE_DATABASE_PASSWORD/$psqlpass/g" $GEONODE_ETC/local_settings.py
}

function setup_django_every_time() {
    pushd $GEONODE_LIB
    virtualenv . --system-site-packages --never-download

    if [ ! -f bin/activate ]
    then
        echo "Creation of virtualenv failed; aborting installation"
        exit -1
    fi

    source bin/activate
    pip install GeoNode-*.zip

    sitedir=`$GEONODE_LIB/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`

    ln -sf $GEONODE_ETC/local_settings.py $sitedir/geonode/local_settings.py
    # Set up logging symlink
    ln -sf /var/log/apache2/error.log $GEONODE_LOG/apache.log

    export DJANGO_SETTINGS_MODULE=geonode.settings
    django-admin.py syncdb --all --noinput
    #django-admin migrate --noinput
    django-admin.py collectstatic --noinput
    django-admin.py loaddata $GEONODE_SHARE/admin.json

    popd
}

function setup_apache_once() {
	chown www-data -R $GEONODE_WWW
	a2enmod proxy_http
	sitedir=`$GEONODE_LIB/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`
        
	sed -i '1d' $APACHE_SITES/geonode
	sed -i "1i WSGIDaemonProcess geonode user=www-data threads=15 processes=2 python-path=$sitedir" $APACHE_SITES/geonode

	#FIXME: This could be removed if setup_apache_every_time is called after setup_apache_once
	$APACHE_SERVICE restart
}

function setup_apache_every_time() {
	a2dissite default

	#FIXME: This could be removed if setup_apache_every_time is called after setup_apache_once
	a2enmod proxy_http

	a2ensite geonode
	$APACHE_SERVICE restart
}

function one_time_setup() {
    psqlpass=$(randpass 8 0)
    secretkey=$(randpass 18 0)

    setup_postgres_once
    setup_django_once
    # setup_apache_once # apache setup needs the every_time django setup since
    # it uses that to get the sitedir location
}

function postinstall() {
    setup_postgres_every_time
    setup_django_every_time
    setup_apache_every_time
    $TOMCAT_SERVICE restart
    $APACHE_SERVICE restart
}

function once() {
    echo "Still need to implement the onetime setup."
    exit 1
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
        once)
                echo "Running GeoNode initial configuration ..."
                one_time_setup
                ;;
	post)
		echo "Running GeoNode postinstall ..."
		postinstall
		;;
        setup_apache_once)
                echo "Configuring Apache ..."
                setup_apache_once
        ;;
	all)
		echo "Running GeoNode installation ..."
		preinstall
                one_time_setup
		postinstall
                setup_apache_once
		;;
	*)
	        printf "\tValid values for step parameter are: 'pre', 'post','all'\n"
		printf "\tDefault value for step is 'all'\n"
		;;
esac
