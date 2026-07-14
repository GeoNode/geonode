FROM ubuntu:24.04

## Enable postgresql-client-15
RUN apt-get update -y && apt-get install curl wget unzip gnupg2 -y
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
# will install python3.10
RUN apt-get install lsb-release -y
RUN echo "deb https://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |tee  /etc/apt/sources.list.d/pgdg.list

# Prepraing dependencies
RUN apt-get install -y \
    libgdal-dev libpq-dev libxml2-dev \
    libxml2 libxslt1-dev zlib1g-dev libjpeg-dev \
    libmemcached-dev libldap2-dev libsasl2-dev libffi-dev

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    gcc vim zip gettext geoip-bin cron \
    postgresql-client-15 \
    python3-all-dev python3-dev \
    python3-gdal python3-psycopg2 python3-ldap \
    python3-pip python3-lxml \
    uwsgi uwsgi-plugin-python3 python3-gdbm python3-venv python-is-python3 gdal-bin

RUN apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils
# RUN git clone https://salsa.debian.org/debian-gis-team/proj.git /tmp/proj
# RUN cd /tmp/proj && debuild -i -us -uc -b && dpkg -i ../*.deb

RUN python -m venv /usr/src/venv
ENV PATH="/usr/src/venv/bin:$PATH"
RUN . /usr/src/venv/bin/activate

# Install pip packages
RUN pip3 install uwsgi \
    && pip install pip --upgrade \
    && pip install wheel==0.38.1 \
    && pip install invoke==2.2.0 \
    && pip install GDAL==3.8.4

# Create symlink for "invoke" command 
# Required after installing via pip inside a virtualenv and avoid changing the 
# entrypoint.sh in existing GeoNode Projects where /usr/local/bin/invoke is used
RUN ln -s $(which invoke) /usr/local/bin/invoke

# Install "sherlock" to be used with "memcached"
RUN pip install sherlock

# Cleanup apt update lists
RUN rm -rf /var/lib/apt/lists/*
