#!/bin/bash
set -e

/usr/local/bin/invoke update >> /usr/src/app/invoke.log

source /root/.override_env

echo DATABASE_URL=$DATABASE_URL
echo GEODATABASE_URL=$GEODATABASE_URL

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

    cmd="uwsgi --ini /usr/src/app/uwsgi.ini"
    echo "Executing UWSGI server $@ for Production"

fi

exec $cmd
