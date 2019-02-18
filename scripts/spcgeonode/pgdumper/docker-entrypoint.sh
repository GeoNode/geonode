#!/bin/sh

envsubst '\$DATABASE_URL' < crontab.envsubst > crontab
/usr/bin/crontab crontab
rm crontab crontab.envsubst

exec "$@"
