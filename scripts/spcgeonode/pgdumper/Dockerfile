FROM python:2.7.13-alpine3.6
 
# 1-2. Install system dependencies (we only need the pg_dump binary from postgresql, other dependencies are in postgresql-client)
RUN apk add --no-cache postgresql-client && \
    apk add --no-cache --virtual BUIID_DEPS postgresql && \
    cp /usr/bin/pg_dump /bin/pg_dump && \
    apk del BUIID_DEPS

# envsubst dependency
RUN apk add --no-cache gettext

# The entrypoint creates the certificate
ADD crontab crontab.envsubst
ADD docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

# We run cron in foreground to update the certificates
CMD ["/usr/sbin/crond", "-f"]
