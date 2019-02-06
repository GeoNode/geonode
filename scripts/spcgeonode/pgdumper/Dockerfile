FROM python:2.7.13-alpine3.6
 
# 1-2. Install system dependencies (we only need the pg_dump binary from postgresql, other dependencies are in postgresql-client)
RUN apk add --no-cache postgresql-client && \
    apk add --no-cache --virtual BUIID_DEPS postgresql && \
    cp /usr/bin/pg_dump /bin/pg_dump && \
    apk del BUIID_DEPS


# The entrypoint creates the certificate
ADD crontab crontab 
RUN /usr/bin/crontab crontab
RUN rm crontab

# We run cron in foreground to update the certificates
CMD ["/usr/sbin/crond", "-f"]
