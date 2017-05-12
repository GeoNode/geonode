FROM python:2.7.9

# This section is borrowed from the official Django image but adds GDAL and others
RUN apt-get update && apt-get install -y \
        gcc \
        gettext \
        postgresql-client libpq-dev \
        sqlite3 \
        python-gdal python-psycopg2 \
        python-imaging python-lxml \
        python-dev libgdal-dev \
        python-ldap \
        libmemcached-dev libsasl2-dev zlib1g-dev \
        python-pylibmc \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install pg client
ENV POSTGRES_VERSION 9.5
RUN apt-get update \
   && apt-get install -y wget \
   && echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/postgres.list \
   && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
   && apt-get update \
   && apt-get install -y postgresql-client-${POSTGRES_VERSION}

COPY package/docker/wait-for-postgres.sh /usr/bin/wait-for-postgres
RUN chmod +x /usr/bin/wait-for-postgres

RUN mkdir /docker-entrypoint.d
COPY package/docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY package/docker/00-bootstrap-dbs.sh /docker-entrypoint.d/

# To understand the next section (the need for requirements.txt and setup.py)
# Please read: https://packaging.python.org/requirements/

# Update pip
RUN pip install --upgrade pip

# python-gdal does not seem to work, let's install manually the version that is
# compatible with the provided libgdal-dev
RUN pip install GDAL==1.10 --global-option=build_ext --global-option="-I/usr/include/gdal"

# Install geonode code and dependencies
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --no-deps -e /usr/src/app/

# Install geonode configuration
VOLUME ["/mnt/geonode_config", "/mnt/geonode_data"]
RUN mkdir -p /mnt/geonode_data/uploaded /mnt/geonode_data/static /mnt/geonode_config \
  && cd /usr/src/app/geonode/ \
  && mv local_settings.py /mnt/geonode_config/ \
  && ln -s /mnt/geonode_config/local_settings.py

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
