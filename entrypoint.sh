#!/bin/bash

# Exit script in case of error
set -e

# Parse bools
parse_bool () {
    case $1 in
        [Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]|[Oo][Nn]|1) echo 'true';;
        *) echo 'false';;
    esac
}

INVOKE_LOG_STDOUT=${INVOKE_LOG_STDOUT:-false}

invoke () {
    if [ $(parse_bool $INVOKE_LOG_STDOUT) = 'true' ]; then
        /usr/local/bin/invoke $@
    else
        /usr/local/bin/invoke $@ > /var/log/geonode/invoke.log 2>&1
    fi
    echo "$@ tasks done"
}

# Start cron && memcached services
# Not necessary, because cron jobs coiuld be run by the docker host, or use a Cronjob in Kubernetes
# Shoud be fine if we remove cron from base image.
# service cron restart

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING DJANGO ENTRYPOINT $(date)"
echo "-----------------------------------------------------"

# check if user exists in passwd file
# if not, change HOME to /tmp
HAS_USER=$(getent passwd $(id -u) | wc -l)
if [ $HAS_USER -eq 1 ]; then
    echo "User $_USER exists in passwd file"

    if [ $HOME = "/" ]; then
        echo "HOME is /, changing to /tmp"
        export HOME=/tmp
    fi
else
    echo "User does not exist in passwd file, changing HOME to /tmp"
    export HOME=/tmp
fi
unset HAS_USER

invoke update

# Preserving the original behavior. 
if [ ! -e $HOME/.bashrc ]; then
    echo "No $HOME/.bashrc found, using skeleton"
    cp /etc/skel/.bashrc $HOME/.bashrc
fi

source $HOME/.bashrc

# Load the environment variables, if exists
if [ -e $HOME/.override_env ]; then
    source $HOME/.override_env
fi

echo DOCKER_API_VERSION=$DOCKER_API_VERSION
echo POSTGRES_USER=$POSTGRES_USER
echo POSTGRES_PASSWORD=$POSTGRES_PASSWORD
echo DATABASE_URL=$DATABASE_URL
echo GEODATABASE_URL=$GEODATABASE_URL
echo SITEURL=$SITEURL
echo ALLOWED_HOSTS=$ALLOWED_HOSTS
echo GEOSERVER_PUBLIC_LOCATION=$GEOSERVER_PUBLIC_LOCATION
echo MONITORING_ENABLED=$MONITORING_ENABLED
echo MONITORING_HOST_NAME=$MONITORING_HOST_NAME
echo MONITORING_SERVICE_NAME=$MONITORING_SERVICE_NAME
echo MONITORING_DATA_TTL=$MONITORING_DATA_TTL

# invoke waitfordbs

cmd="$@"

if [ $(parse_bool $IS_CELERY) = 'true' ]; then
    echo "Executing Celery server $cmd for Production"

else
    invoke migrations
    invoke prepare

    if [ $(parse_bool $FORCE_REINIT) = 'true' ]  || [ ! -e "/mnt/volumes/statics/geonode_init.lock" ]; then
        invoke fixtures
        invoke monitoringfixture
        invoke initialized
        invoke updateadmin
    fi

    invoke statics

    echo "Executing UWSGI server $cmd for Production"
fi

echo "-----------------------------------------------------"
echo "FINISHED DJANGO ENTRYPOINT --------------------------"
echo "-----------------------------------------------------"

# Run the CMD 
echo "got command $cmd"
exec $cmd
