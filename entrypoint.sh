#!/bin/bash
set -e

/usr/local/bin/invoke update >> /usr/src/app/invoke.log

source $HOME/.bashrc
source $HOME/.override_env

echo DOCKER_API_VERSION=$DOCKER_API_VERSION
echo DATABASE_URL=$DATABASE_URL
echo GEODATABASE_URL=$GEODATABASE_URL
echo SITEURL=$SITEURL
echo ALLOWED_HOSTS=$ALLOWED_HOSTS
echo GEOSERVER_PUBLIC_LOCATION=$GEOSERVER_PUBLIC_LOCATION
echo MONITORING_ENABLED=$MONITORING_ENABLED
echo MONITORING_HOST_NAME=$MONITORING_HOST_NAME
echo MONITORING_SERVICE_NAME=$MONITORING_SERVICE_NAME
echo MONITORING_DATA_TTL=$MONITORING_DATA_TTL

/usr/local/bin/invoke waitfordbs >> /usr/src/app/invoke.log
echo "waitfordbs task done"

echo "running migrations"
/usr/local/bin/invoke migrations >> /usr/src/app/invoke.log
echo "migrations task done"

cmd="$@"

echo DOCKER_ENV=$DOCKER_ENV

if [ -z ${DOCKER_ENV} ] || [ ${DOCKER_ENV} = "development" ]
then

    /usr/local/bin/invoke prepare
    echo "prepare task done"
    /usr/local/bin/invoke fixtures
    echo "fixture task done"

    if [ ${IS_CELERY} = "true" ] || [ ${IS_CELERY} = "True" ]
    then

        cmd=$cmd
        echo "Executing Celery server $cmd for Development"

    else

        echo "install requirements for development"
        /usr/local/bin/invoke devrequirements
        echo "refresh static data"
        /usr/local/bin/invoke statics
        echo "static data refreshed"
        cmd=$cmd
        echo "Executing standard Django server $cmd for Development"

    fi

else
    if [ ${IS_CELERY} = "true" ]  || [ ${IS_CELERY} = "True" ]
    then
        cmd=$CELERY_CMD
        echo "Executing Celery server $cmd for Production"
    else

        /usr/local/bin/invoke prepare >> /usr/src/app/invoke.log
        echo "prepare task done"

        if [ ! -e "/mnt/volumes/statics/geonode_init.lock" ]; then
            /usr/local/bin/invoke updategeoip >> /usr/src/app/invoke.log
            echo "updategeoip task done"
            /usr/local/bin/invoke fixtures >> /usr/src/app/invoke.log
            echo "fixture task done"
            /usr/local/bin/invoke monitoringfixture >> /usr/src/app/invoke.log
            echo "monitoringfixture task done"
            /usr/local/bin/invoke initialized >> /usr/src/app/invoke.log
            echo "initialized"
        fi

        echo "refresh static data"
        /usr/local/bin/invoke statics >> /usr/src/app/invoke.log
        echo "static data refreshed"
        /usr/local/bin/invoke waitforgeoserver >> /usr/src/app/invoke.log
        echo "waitforgeoserver task done"
        /usr/local/bin/invoke geoserverfixture >> /usr/src/app/invoke.log
        echo "geoserverfixture task done"
        /usr/local/bin/invoke updateadmin >> /usr/src/app/invoke.log
        echo "updateadmin task done"

        cmd=$UWSGI_CMD
        echo "Executing UWSGI server $cmd for Production"
    fi
fi
echo "got command $cmd"
exec $cmd
