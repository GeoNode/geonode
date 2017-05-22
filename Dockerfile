FROM geonode/django

# Install pg client
ENV POSTGRES_VERSION 9.5
RUN apt-get update \
   && apt-get install -y wget \
   && echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/postgres.list \
   && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
   && apt-get update \
   && apt-get install -y postgresql-client-${POSTGRES_VERSION}

RUN mkdir /docker-entrypoint.d
COPY package/docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY package/docker/00-bootstrap-dbs.sh /docker-entrypoint.d/

# Install geonode configuration in named volume
RUN mkdir -p /mnt/geonode_data/uploaded /mnt/geonode_data/static /mnt/geonode_config \
  && cd /usr/src/app/geonode/ \
  && mv local_settings.py.docker /mnt/geonode_config/local_settings.py \
  && ln -s /mnt/geonode_config/local_settings.py

VOLUME ["/mnt/geonode_config", "/mnt/geonode_data"]

ENTRYPOINT ["/docker-entrypoint.sh"]

