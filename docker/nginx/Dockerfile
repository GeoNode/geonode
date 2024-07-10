ARG BASE_IMAGE_VERSION
FROM 52north/geonode-nginx:${BASE_IMAGE_VERSION}

COPY ./cert.pem /geonode-certificates/autoissued/fullchain.pem
COPY ./key.pem /geonode-certificates/autoissued/privkey.pem

# overwrite nginx conf for hardening
COPY ./nginx.https.available.conf.envsubst /etc/nginx/nginx.https.available.conf.envsubst