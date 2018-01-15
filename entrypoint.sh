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

exec "$@"
