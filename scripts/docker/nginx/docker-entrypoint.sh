#!/bin/sh

# Exit script in case of error
set -e

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING NGINX ENTRYPOINT ---------------------------"
date

# We make the config dir
mkdir -p "/geonode-certificates/$LETSENCRYPT_MODE"

echo "Creating autoissued certificates for HTTP host"
if [ ! -f "/geonode-certificates/autoissued/privkey.pem" ] || [[ $(find /geonode-certificates/autoissued/privkey.pem -mtime +365 -print) ]]; then
        echo "Autoissued certificate does not exist or is too old, we generate one"
        mkdir -p "/geonode-certificates/autoissued/"
        openssl req -x509 -nodes -days 1825 -newkey rsa:2048 -keyout "/geonode-certificates/autoissued/privkey.pem" -out "/geonode-certificates/autoissued/fullchain.pem" -subj "/CN=${HTTP_HOST:-HTTPS_HOST}" 
else
        echo "Autoissued certificate already exists"
fi

echo "Creating symbolic link for HTTPS certificate"
# for some reason, the ln -f flag doesn't work below...
# TODO : not DRY (reuse same scripts as docker-autoreload.sh)
rm -f /certificate_symlink
if [ -f "/geonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST/fullchain.pem" ] && [ -f "/geonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST/privkey.pem" ]; then
        echo "Certbot certificate exists, we symlink to the live cert"
        ln -sf "/geonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST" /certificate_symlink
else
        echo "Certbot certificate does not exist, we symlink to autoissued"
        ln -sf "/geonode-certificates/autoissued" /certificate_symlink
fi

if [ -z "${HTTPS_HOST}" ]; then
        HTTP_SCHEME="http"
else
        HTTP_SCHEME="https"
fi

export HTTP_SCHEME=${HTTP_SCHEME:-http}
export GEONODE_LB_HOST_IP=${GEONODE_LB_HOST_IP:-django}
export GEONODE_LB_PORT=${GEONODE_LB_PORT:-8000}
export GEOSERVER_LB_HOST_IP=${GEOSERVER_LB_HOST_IP:-geoserver}
export GEOSERVER_LB_PORT=${GEOSERVER_LB_PORT:-8080}

echo "Replacing environement variables"
envsubst '\$HTTP_HOST \$HTTPS_HOST \$HTTP_SCHEME \$GEONODE_LB_HOST_IP \$GEONODE_LB_PORT \$GEOSERVER_LB_HOST_IP \$GEOSERVER_LB_PORT \$RESOLVER' < /etc/nginx/nginx.conf.envsubst > /etc/nginx/nginx.conf
envsubst '\$HTTP_HOST \$HTTPS_HOST \$HTTP_SCHEME \$GEONODE_LB_HOST_IP \$GEONODE_LB_PORT \$GEOSERVER_LB_HOST_IP \$GEOSERVER_LB_PORT \$RESOLVER' < /etc/nginx/nginx.https.available.conf.envsubst > /etc/nginx/nginx.https.available.conf
envsubst '\$HTTP_HOST \$HTTPS_HOST \$HTTP_SCHEME \$GEONODE_LB_HOST_IP \$GEONODE_LB_PORT \$GEOSERVER_LB_HOST_IP \$GEOSERVER_LB_PORT' < /etc/nginx/sites-enabled/geonode.conf.envsubst > /etc/nginx/sites-enabled/geonode.conf

echo "Enabling or not https configuration"
if [ -z "${HTTPS_HOST}" ]; then
        echo "" > /etc/nginx/nginx.https.enabled.conf
else
        ln -sf /etc/nginx/nginx.https.available.conf /etc/nginx/nginx.https.enabled.conf
fi

echo "Loading nginx autoreloader"
sh /docker-autoreload.sh &

echo "-----------------------------------------------------"
echo "FINISHED NGINX ENTRYPOINT ---------------------------"
echo "-----------------------------------------------------"

# Run the CMD 
exec "$@"
