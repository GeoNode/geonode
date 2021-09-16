#!/bin/sh

# Exit script in case of error
set -e

echo $"\n\n\n"
echo "-----------------------------------------------------"
echo "STARTING LETSENCRYPT ENTRYPOINT ---------------------"
date

# We make the config dir
mkdir -p "/spcgeonode-certificates/$LETSENCRYPT_MODE"

# Do not exit script in case of error
set +e

# We run the command
if [ "$LETSENCRYPT_MODE" == "staging" ]; then
    printf "\nTrying to get STAGING certificate\n"
    certbot --config-dir "/spcgeonode-certificates/$LETSENCRYPT_MODE" certonly --webroot -w "/spcgeonode-certificates" -d "$HTTPS_HOST" -m "$ADMIN_EMAIL" --agree-tos --non-interactive --staging --server https://acme-v02.api.letsencrypt.org/directory
elif [ "$LETSENCRYPT_MODE" == "production" ]; then
    printf "\nTrying to get PRODUCTION certificate\n"
    certbot --config-dir "/spcgeonode-certificates/$LETSENCRYPT_MODE" certonly --webroot -w "/spcgeonode-certificates" -d "$HTTPS_HOST" -m "$ADMIN_EMAIL" --agree-tos --non-interactive --server https://acme-v02.api.letsencrypt.org/directory
else
    printf "\nNot trying to get certificate (simulating failure, because LETSENCRYPT_MODE variable was neither staging nor production\n"
    /bin/false
fi

# If the certbot comand failed, we will create a placeholder certificate
if [ ! $? -eq 0 ]; then
    # Exit script in case of error
    set -e

    printf "\nFailed to get the certificates !\n"

    printf "\nWaiting 30s to avoid hitting Letsencrypt rate limits before it's even possible to react\n"
    sleep 30

    exit 1
fi

printf "\nCertificate have been created/renewed successfully\n"

echo "-----------------------------------------------------"
echo "FINISHED LETSENCRYPT ENTRYPOINT ---------------------"
echo "-----------------------------------------------------"

# Run the CMD
exec "$@"
