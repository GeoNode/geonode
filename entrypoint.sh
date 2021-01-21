#!/bin/bash

# Exit script in case of error
set -e

# Start cron && memcached services
service cron restart
service memcached restart

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING DJANGO ENTRYPOINT $(date)"
echo "-----------------------------------------------------"

/usr/local/bin/invoke update > /usr/src/geonode/invoke.log 2>&1

source $HOME/.bashrc
source $HOME/.override_env

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

/usr/local/bin/invoke waitfordbs > /usr/src/geonode/invoke.log 2>&1
echo "waitfordbs task done"

echo "running migrations"
/usr/local/bin/invoke migrations > /usr/src/geonode/invoke.log 2>&1
echo "migrations task done"

cmd="$@"

echo DOCKER_ENV=$DOCKER_ENV

if [ -z ${DOCKER_ENV} ] || [ ${DOCKER_ENV} = "development" ]
then

    /usr/local/bin/invoke prepare > /usr/src/geonode/invoke.log 2>&1
    echo "prepare task done"
    /usr/local/bin/invoke fixtures > /usr/src/geonode/invoke.log 2>&1
    echo "fixture task done"

    if [ ${IS_CELERY} = "true" ] || [ ${IS_CELERY} = "True" ]
    then

        echo "Executing Celery server $cmd for Development"

    else

        echo "install requirements for development"
        /usr/local/bin/invoke devrequirements > /usr/src/geonode/invoke.log 2>&1
        echo "refresh static data"
        /usr/local/bin/invoke statics > /usr/src/geonode/invoke.log 2>&1
        echo "static data refreshed"

        echo "Executing standard Django server $cmd for Development"

    fi

else
    if [ ${IS_CELERY} = "true" ]  || [ ${IS_CELERY} = "True" ]
    then
        echo "Executing Celery server $cmd for Production"
    else

        /usr/local/bin/invoke prepare > /usr/src/geonode/invoke.log 2>&1
        echo "prepare task done"

        if [ ${FORCE_REINIT} = "true" ]  || [ ${FORCE_REINIT} = "True" ] || [ ! -e "/mnt/volumes/statics/geonode_init.lock" ]; then
            /usr/local/bin/invoke updategeoip > /usr/src/geonode/invoke.log 2>&1
            echo "updategeoip task done"
            /usr/local/bin/invoke fixtures > /usr/src/geonode/invoke.log 2>&1
            echo "fixture task done"
            /usr/local/bin/invoke monitoringfixture > /usr/src/geonode/invoke.log 2>&1
            echo "monitoringfixture task done"
            /usr/local/bin/invoke initialized > /usr/src/geonode/invoke.log 2>&1
            echo "initialized"
        fi

        echo "refresh static data"
        /usr/local/bin/invoke statics > /usr/src/geonode/invoke.log 2>&1
        echo "static data refreshed"
        /usr/local/bin/invoke waitforgeoserver > /usr/src/geonode/invoke.log 2>&1
        echo "waitforgeoserver task done"
        /usr/local/bin/invoke geoserverfixture > /usr/src/geonode/invoke.log 2>&1
        echo "geoserverfixture task done"
        /usr/local/bin/invoke updateadmin > /usr/src/geonode/invoke.log 2>&1
        echo "updateadmin task done"

        echo "Executing UWSGI server $cmd for Production"
    fi
fi

echo "-----------------------------------------------------"
echo "FINISHED DJANGO ENTRYPOINT --------------------------"
echo "-----------------------------------------------------"

# Run the CMD 
echo "got command $cmd"
exec $cmd
