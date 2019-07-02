FROM alpine:3.6

# 1-2. Install system dependencies
RUN apk add --no-cache certbot py-pip && pip install pyopenssl==16.0.0

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
