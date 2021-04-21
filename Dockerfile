FROM python:3.8.9-buster
LABEL GeoNode development team

RUN mkdir -p /usr/src/geonode

# Enable postgresql-client-13
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list
RUN echo "deb http://deb.debian.org/debian/ stable main contrib non-free" | tee /etc/apt/sources.list.d/debian.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# This section is borrowed from the official Django image but adds GDAL and others
RUN apt-get update && apt-get install -y \
    libgdal-dev libpq-dev libxml2-dev \
    libxml2 libxslt1-dev zlib1g-dev libjpeg-dev \
    libmemcached-dev libldap2-dev libsasl2-dev libffi-dev

RUN apt-get update && apt-get install -y \
    gcc zip gettext geoip-bin cron \
    postgresql-client-13 \
    sqlite3 spatialite-bin libsqlite3-mod-spatialite \
    python3-dev python3-gdal python3-psycopg2 python3-ldap \
    python3-pip python3-pil python3-lxml python3-pylibmc \
    uwsgi uwsgi-plugin-python3 \
    firefox-esr \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# GDAL upgrade to fix this issue https://github.com/OSGeo/gdal/issues/1692
# proj-7 && gdal 3.2.1 installation should be removed if base image upgraded to Bullseye
# install proj-7
WORKDIR /usr/src
RUN wget https://download.osgeo.org/proj/proj-7.2.1.tar.gz
RUN tar xvzf proj-7.2.1.tar.gz
WORKDIR ./proj-7.2.1
RUN ./configure --without-curl
RUN make && make install

# Download GDAL v3.2.1 Source (ex. 3.2.1)
WORKDIR /usr/src
ENV CPUS 2
ENV GDAL_SHORT_VERSION 3.2.1
ENV GDAL_VERSION 3.2.1
RUN wget -q https://download.osgeo.org/gdal/${GDAL_SHORT_VERSION}/gdal-${GDAL_VERSION}.tar.gz
RUN tar -xzf gdal-${GDAL_VERSION}.tar.gz && cd gdal-${GDAL_SHORT_VERSION} && \
    ./configure \
    --disable-debug \
    --prefix=/usr/local \
    --disable-static \
    --with-curl=/usr/local/bin/curl-config \
    --with-geos \
    #--with-geotiff=/usr/local \
    --with-hide-internal-symbols=yes \
    #--with-libtiff=/usr/local \
    --with-jpeg=/usr/local \
    --with-png \
    #--with-openjpeg \
    --with-sqlite3 \
    --with-proj=/usr/local \
    #--with-rename-internal-libgeotiff-symbols=yes \
    #--with-rename-internal-libtiff-symbols=yes \
    --with-threads=yes \
    --with-webp=/usr/local \
    #--with-zstd=/usr/local \
    #--with-libdeflate \
    && echo "building GDAL ${GDAL_VERSION}..." \
    && make -j${CPUS} && make --quiet install


# add bower and grunt command
COPY . /usr/src/geonode/
WORKDIR /usr/src/geonode

COPY monitoring-cron /etc/cron.d/monitoring-cron
RUN chmod 0644 /etc/cron.d/monitoring-cron
RUN crontab /etc/cron.d/monitoring-cron
RUN touch /var/log/cron.log
RUN service cron start

COPY wait-for-databases.sh /usr/bin/wait-for-databases
RUN chmod +x /usr/bin/wait-for-databases
RUN chmod +x /usr/src/geonode/tasks.py \
    && chmod +x /usr/src/geonode/entrypoint.sh

COPY celery.sh /usr/bin/celery-commands
RUN chmod +x /usr/bin/celery-commands

# Prepraing dependencies
RUN apt-get update && apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils
# RUN git clone https://salsa.debian.org/debian-gis-team/proj.git /tmp/proj
# RUN cd /tmp/proj && debuild -i -us -uc -b && dpkg -i ../*.deb

# Install pip packages
RUN pip install pip --upgrade
RUN pip install --upgrade --no-cache-dir  --src /usr/src -r requirements.txt \
    && pip install pygdal==$(gdal-config --version).* \
    && pip install flower==0.9.4

RUN pip install --upgrade  -e .

# Activate "memcached"
RUN apt install memcached
RUN pip install pylibmc \
    && pip install sherlock

# Install "geonode-contribs" apps
RUN cd /usr/src; git clone https://github.com/GeoNode/geonode-contribs.git -b master
# Install logstash and centralized dashboard dependencies
RUN cd /usr/src/geonode-contribs/geonode-logstash; pip install --upgrade  -e . \
    cd /usr/src/geonode-contribs/ldap; pip install --upgrade  -e .

# Export ports
EXPOSE 8000

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
# ENTRYPOINT service cron restart && service memcached restart && /usr/src/geonode/entrypoint.sh
