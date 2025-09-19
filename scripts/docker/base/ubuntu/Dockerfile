FROM ubuntu:22.04

RUN mkdir -p /usr/src/geonode

## Enable postgresql-client-15
RUN apt-get update -y && apt-get install curl wget unzip gnupg2 -y
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
# will install python3.10
RUN apt-get install lsb-core -y
RUN echo "deb https://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |tee  /etc/apt/sources.list.d/pgdg.list

# Prepraing dependencies
RUN apt-get install -y \
    libpq-dev libxml2-dev libproj-dev \
    libxml2 libxslt1-dev zlib1g-dev libjpeg-dev \
    libmemcached-dev libldap2-dev libsasl2-dev libffi-dev

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    gcc vim zip gettext geoip-bin cron \
    postgresql-client-15 \
    python3-all-dev python3-dev \
    python3-psycopg2 python3-ldap \
    python3-pip python3-lxml \
    uwsgi uwsgi-plugin-python3 python3-gdbm python-is-python3 cmake

RUN apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils
# RUN git clone https://salsa.debian.org/debian-gis-team/proj.git /tmp/proj
# RUN cd /tmp/proj && debuild -i -us -uc -b && dpkg -i ../*.deb

WORKDIR /tmp
RUN wget https://download.osgeo.org/gdal/3.11.4/gdal-3.11.4.tar.gz
RUN tar -xvf gdal-3.11.4.tar.gz
RUN cd gdal-3.11.4
RUN mkdir build
RUN cd build
RUN cmake /tmp/gdal-3.11.4
RUN cmake --build . --parallel 8
RUN cmake --build . --parallel 8 --target install
RUN ldconfig

WORKDIR /usr/src/geonode


# Install pip packages
RUN pip3 install uwsgi \
    && pip install pip --upgrade \
    && pip install wheel==0.38.1 \
    && pip install GDAL==$(gdal-config --version).*

# Install "sherlock" to be used with "memcached"
RUN pip install sherlock

# Cleanup apt update lists
RUN rm -rf /var/lib/apt/lists/*
