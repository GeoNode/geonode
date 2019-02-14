#!/bin/sh

# Exit script in case of error
set -e

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING DJANGO ENTRYPOINT $(date)"
echo "-----------------------------------------------------"

# Setting dynamic env vars (some of this could probably be put in docker-compose once
# https://github.com/docker/compose/pull/5268 is merged, or even better hardcoded if
# geonode supported relative site urls)
if [ ! -z "$HTTPS_HOST" ]; then
    export SITEURL="https://$HTTPS_HOST"
    if [ "$HTTPS_PORT" != "443" ]; then
        SITEURL="$SITEURL:$HTTPS_PORT"
    fi
else
    export SITEURL="http://$HTTP_HOST"
    if [ "$HTTP_PORT" != "80" ]; then
        SITEURL="$SITEURL:$HTTP_PORT"
    fi
fi

export GEOSERVER_PUBLIC_LOCATION="${SITEURL}/geoserver/"

# Run migrations
echo 'Running initialize.py...'
python -u scripts/spcgeonode/django/initialize.py

echo "-----------------------------------------------------"
echo "FINISHED DJANGO ENTRYPOINT --------------------------"
echo "-----------------------------------------------------"

# Run the CMD 
exec "$@"
