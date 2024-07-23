FROM alpine:latest

RUN apk add --no-cache certbot 

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
