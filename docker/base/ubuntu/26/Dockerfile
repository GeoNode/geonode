FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/src/geonode

## Enable PostgreSQL apt repo (PGDG)
RUN apt-get update -y && apt-get install -y curl wget unzip gnupg2 lsb-release ca-certificates
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg
# PGDG has no repo for 26.04's codename yet; pin to a supported one.
RUN echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt/ noble-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update -y

# Preparing dependencies
RUN apt-get install -y \
    libgdal-dev libpq-dev libxml2-dev \
    libxslt1-dev zlib1g-dev libjpeg-dev \
    libldap2-dev libsasl2-dev libffi-dev git

RUN apt-get install -y --no-install-recommends \
    gcc vim zip gettext geoip-bin cron \
    postgresql-client-15 \
    python3-all-dev python3-dev \
    python3-gdal python3-psycopg2 python3-ldap \
    python3-pip python3-lxml \
    uwsgi uwsgi-plugin-python3 python3-gdbm python3-venv python-is-python3 gdal-bin

RUN apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils libcrypt-dev

RUN python -m venv /usr/src/venv
ENV PATH="/usr/src/venv/bin:$PATH"

# Install pip packages
RUN pip install uwsgi \
    && pip install pip --upgrade \
    && pip install wheel==0.38.1 \
    && pip install invoke==2.2.0 \
    && pip install GDAL==3.12.2

# Symlink for "invoke" so existing entrypoint.sh paths (/usr/local/bin/invoke) keep working
RUN ln -s $(which invoke) /usr/local/bin/invoke

# Install "sherlock" for use with "redis cache"
RUN pip install sherlock

# Cleanup apt lists
RUN rm -rf /var/lib/apt/lists/*
