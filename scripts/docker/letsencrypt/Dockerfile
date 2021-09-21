FROM alpine:3.8

# 1-2. Install system dependencies
RUN apk add --no-cache certbot py-pip && pip install pyopenssl==16.0.0 # Need to downgrade PyOpenSSL to 16.0.0 to avoid conflicts and solve the cryptography error : https://github.com/plesk/letsencrypt-plesk/issues/117


# Installing scripts
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Installing cronjobs
ADD crontab /crontab
RUN /usr/bin/crontab /crontab && \
    rm /crontab

# Setup the entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# We run cron in foreground to update the certificates
CMD /usr/sbin/crond -f
