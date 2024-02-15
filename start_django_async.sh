#!/bin/bash
set -e

export RESOURCE_PUBLISHING=True
export ADMIN_MODERATE_UPLOADS=True
export NOTIFICATION_ENABLED=True
export MONITORING_ENABLED=False
export EMAIL_ENABLED=True
export BROKER_URL=amqp://guest:guest@localhost:5672/
export ASYNC_SIGNALS=True
export DJANGO_SETTINGS_MODULE=geonode.local_settings

do_migrations=0

while getopts "m" opt
do
    case $opt in
    (m) do_migrations=1 ;;
    (*) printf "Illegal option '-%s'\n" "$opt" && printf "Example usage: ./start_django_async.sh -m\n  Options:\n\t(m) Runs migrations\n\t\n" && exit 1 ;;
    esac
done

(( do_migrations )) && paver sync
paver start_django
