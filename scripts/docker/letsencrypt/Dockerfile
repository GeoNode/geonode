FROM certbot/certbot:v1.21.0

# Installing scripts
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Installing cronjobs
ADD crontab /crontab
RUN /usr/bin/crontab /crontab && \
    rm /crontab

# Setup the entrypoint
WORKDIR /
ENTRYPOINT ["./docker-entrypoint.sh"]

# We run cron in foreground to update the certificates
CMD /usr/sbin/crond -f
