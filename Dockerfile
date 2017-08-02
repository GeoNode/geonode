FROM python:2.7

ENV POSTGRES_VERSION 9.5

# This section is borrowed from the official Django image but adds GDAL and others
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main" > /etc/apt/sources.list.d/postgres.list \
 && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
 && apt-get update && apt-get install -y \
        gcc \
        gettext \
        postgresql-client-${POSTGRES_VERSION} libpq-dev \
        sqlite3 \
        python-gdal python-psycopg2 \
        python-imaging python-lxml \
        python-dev libgdal-dev \
        python-ldap \
        libmemcached-dev libsasl2-dev zlib1g-dev \
        python-pylibmc \
        wget \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

COPY package/docker/ /

# Update pip
RUN pip install --upgrade pip \
# python-gdal does not seem to work, let's install manually the version that is
# compatible with the provided libgdal-dev
    && pip install GDAL==1.10 --global-option=build_ext --global-option="-I/usr/include/gdal" \
# install gunicorn for production setup
    && pip install gunicorn

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["django-admin.py", "runserver", "0.0.0.0:8000", "--settings=geonode.settings"]

# Install tools for frontend (node, npm, grunt, bower, ...)
ADD https://nodejs.org/dist/v6.11.2/node-v6.11.2-linux-x64.tar.xz /usr/local/
RUN cd /usr/local/ \
  && wget https://nodejs.org/dist/v6.11.2/node-v6.11.2-linux-x64.tar.xz \
  && tar Jxvf node-v6.11.2-linux-x64.tar.xz \
  && rm node-v6.11.2-linux-x64.tar.xz \
  && ln -s node-v6.11.2-linux-x64 node \
  && cd /usr/local/bin \
  && ln -s /usr/local/node-v6.11.2-linux-x64/bin/node \
  && ln -s /usr/local/node-v6.11.2-linux-x64/bin/npm \
  && npm install npm@latest -g \
  && npm install -g bower \
  && npm install -g grunt

ENV PATH=/usr/local/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Install geonode code and dependencies
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app/
RUN pip install --no-cache-dir --no-deps -e /usr/src/app/ \
  && cd /usr/src/app/geonode/static \
  && npm install \
  && grunt production

# Install geonode configuration
RUN mkdir -p /mnt/geonode_data/uploaded /mnt/geonode_data/static /mnt/geonode_config \
  && cd /usr/src/app/geonode/ \
  && cp local_settings.py.docker /mnt/geonode_config/local_settings.py \
  && ln -s /mnt/geonode_config/local_settings.py

VOLUME ["/mnt/geonode_config", "/mnt/geonode_data"]
