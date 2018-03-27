#!/bin/bash
set -e

/usr/local/bin/invoke update >> /usr/src/app/invoke.log

source $HOME/.override_env

echo DATABASE_URL=$DATABASE_URL
echo GEODATABASE_URL=$GEODATABASE_URL
echo SITEURL=$SITEURL
echo ALLOWED_HOSTS=$ALLOWED_HOSTS
echo GEOSERVER_PUBLIC_LOCATION=$GEOSERVER_PUBLIC_LOCATION

/usr/local/bin/invoke waitfordbs >> /usr/src/app/invoke.log

echo "waitfordbs task done"

/usr/local/bin/invoke migrations >> /usr/src/app/invoke.log
echo "migrations task done"
/usr/local/bin/invoke prepare >> /usr/src/app/invoke.log
echo "prepare task done"
/usr/local/bin/invoke fixtures >> /usr/src/app/invoke.log
echo "fixture task done"

cmd="$@"

echo DOCKER_ENV=$DOCKER_ENV

if [ -z ${DOCKER_ENV} ] || [ ${DOCKER_ENV} = "development" ]
then

    echo "Executing standard Django server $cmd for Development"

else

    if [ ${IS_CELERY} = "true" ]
    then

        cmd=$CELERY_CMD
        echo "Executing Celery server $cmd for Production"

    else

        cmd=$UWSGI_CMD
        echo "Executing UWSGI server $cmd for Production"

    fi

fi

exec $cmd
