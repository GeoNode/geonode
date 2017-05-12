FROM camptocamp/geonode_django

ENV POSTGRES_VERSION 9.5

# Install multiple version of pg client and tools
RUN apt-get update \
   && apt-get install -y wget \
   && echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/postgres.list \
   && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
   && apt-get update \
   && apt-get install -y postgresql-client-${POSTGRES_VERSION}

RUN rm /usr/src/app/geonode/local_settings.py

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

