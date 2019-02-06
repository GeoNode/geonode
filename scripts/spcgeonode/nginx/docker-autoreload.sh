#!/bin/sh

# This will watch the /spcgeonode-certificates folder and run nginx -s reload whenever there are some changes.
# We use this to reload nginx config when certificates changed.

# inspired/copied from https://github.com/kubernetes/kubernetes/blob/master/examples/https-nginx/auto-reload-nginx.sh

while true
do
        inotifywait -e create -e modify -e delete -e move -r --exclude "\\.certbot\\.lock|\\.well-known" "/spcgeonode-certificates/$LETSENCRYPT_MODE"
        echo "Changes noticed in /spcgeonode-certificates"

        echo "Waiting 5s for additionnal changes"
        sleep 5

        echo "Creating symbolic link for WAN host"
        # for some reason, the ln -f flag doesn't work below...
        rm -f /certificate_symlink
        if [ -f "/spcgeonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST/fullchain.pem" ] && [ -f "/spcgeonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST/privkey.pem" ]; then
                echo "Certbot certificate exists, we symlink to the live cert"
                ln -sf "/spcgeonode-certificates/$LETSENCRYPT_MODE/live/$HTTPS_HOST" /certificate_symlink
        else
                echo "Certbot certificate does not exist, we symlink to autoissued"
                ln -sf "/spcgeonode-certificates/autoissued" /certificate_symlink
        fi

        # Test nginx configuration
        nginx -t
        # If it passes, we reload
        if [ $? -eq 0 ]
        then
                echo "Configuration valid, we reload..."
                nginx -s reload
        else
                echo "Configuration not valid, we do not reload."
        fi
done
