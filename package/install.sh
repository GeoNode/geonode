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
    s)
        stepflag=1
        stepval="$OPTARG"
        ;;
    ?)
        printf "Usage: %s: [-s value] configfile\n" $(basename $0) >&2
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
    mkdir -p $GEONODE_BIN
    mkdir -p $GEONODE_ETC
    mkdir -p $GEONODE_ETC/media
    mkdir -p $GEONODE_ETC/templates
    mkdir -p $GEONODE_SHARE
}

function reorganize_configuration() {
    cp -rp $INSTALL_DIR/support/geonode.apache $APACHE_SITES/geonode.conf
    cp -rp $INSTALL_DIR/support/geonode.wsgi $GEONODE_WWW/wsgi/
    cp -rp $INSTALL_DIR/support/geonode.robots $GEONODE_WWW/robots.txt
    cp -rp $INSTALL_DIR/support/geonode.binary $GEONODE_BIN/geonode
    cp -rp $INSTALL_DIR/support/packages/*.* $GEONODE_SHARE
    cp -rp $INSTALL_DIR/GeoNode*.zip $GEONODE_SHARE
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
createdb -E UTF8 -l en_US.UTF8 -T template0 geonode
createdb -E UTF8 -l en_US.UTF8 -T template0 geonode_data
psql -d geonode_data -c 'CREATE EXTENSION postgis'
EOF
su - postgres -c "psql" <<EOF
CREATE ROLE geonode WITH LOGIN PASSWORD '$psqlpass' SUPERUSER INHERIT;
ALTER USER geonode WITH PASSWORD '$psqlpass';
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
    pip install pip==9.0.3 --quiet
    pip install $GEONODE_SHARE/GeoNode-*.zip --no-dependencies --quiet
    pip install $GEONODE_SHARE/jwcrypto-0.5.0-py2.py3-none-any.whl --no-dependencies --no-cache-dir --quiet
    pip install $GEONODE_SHARE/xmltodict-0.10.2.tar.gz --no-dependencies --no-cache-dir --quiet
    pip install $GEONODE_SHARE/lxml-3.6.2.tar.gz --no-dependencies --no-cache-dir --quiet

    geonodedir=`python -c "import geonode;import os;print os.path.dirname(geonode.__file__)"`

    ln -sf $GEONODE_ETC/local_settings.py $geonodedir/local_settings.py
    # Set up logging symlink
    mkdir -p $GEONODE_LOG
    ln -sf /var/log/apache2/error.log $GEONODE_LOG/apache.log

    export DJANGO_SETTINGS_MODULE=geonode.local_settings

    # django-admin migrate account --settings=geonode.settings
    geonode makemigrations --merge --verbosity 0
    geonode makemigrations --verbosity 0
    # geonode migrate auth --verbosity 0
    # geonode migrate sites --verbosity 0
    # geonode migrate people --verbosity 0
    geonode migrate --verbosity 0
    geonode loaddata $geonodedir/people/fixtures/sample_admin.json
    geonode loaddata $geonodedir/base/fixtures/default_oauth_apps.json
    geonode loaddata $geonodedir/base/fixtures/initial_data.json
    geonode set_all_layers_alternate --verbosity 0
    geonode collectstatic --noinput --verbosity 0

    # Create an empty uploads dir
    mkdir -p $GEONODE_WWW/uploaded
    mkdir -p $GEONODE_WWW/uploaded/documents/
    mkdir -p $GEONODE_WWW/uploaded/layers/
    mkdir -p $GEONODE_WWW/uploaded/thumbs/
    mkdir -p $GEONODE_WWW/uploaded/avatars/
    mkdir -p $GEONODE_WWW/uploaded/people_group/
    mkdir -p $GEONODE_WWW/uploaded/group/
    # Apply the permissions to the newly created folders.
    chown www-data -R $GEONODE_WWW
    # Open up the permissions of the media folders so the python
    # processes like updatelayers and collectstatic can write here
    chmod 777 -R $GEONODE_WWW/uploaded
    chmod 777 -R $GEONODE_WWW/static
}

function setup_apache_once() {
    chown www-data -R $GEONODE_WWW
    a2enmod proxy_http

    sed -i '1d' $APACHE_SITES/geonode.conf
    sed -i "1i WSGIDaemonProcess geonode user=www-data threads=15 processes=2" $APACHE_SITES/geonode.conf

    $APACHE_SERVICE restart
    sleep 15

    $GEONODE_BIN/geonode-updateip -p localhost

    $TOMCAT_SERVICE restart
    sleep 30

}

function setup_apache_every_time() {
    a2dissite 000-default

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

function setup_geoserver() {
    pushd ../
    paver setup
    popd
    mv ../downloaded/geoserver.war $TOMCAT_WEBAPPS
    $TOMCAT_SERVICE restart
}

function postinstall() {
    setup_postgres_every_time
    setup_django_every_time
    setup_apache_every_time
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
        setup_geoserver
        postinstall
        setup_apache_once
        ;;
    *)
        printf "\tValid values for step parameter are: 'pre', 'post','all'\n"
        printf "\tDefault value for step is 'all'\n"
        ;;
esac
