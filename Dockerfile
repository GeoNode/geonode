FROM geonode/geonode-base:latest-ubuntu-26.04

# Some label best practices
# https://www.docker.com/blog/docker-best-practices-using-tags-and-labels-to-manage-docker-image-sprawl/
LABEL org.opencontainers.image.title="GeoNode" \
    org.opencontainers.image.version=${GEONODE_VERSION} \
    org.opencontainers.image.vendor="GeoNode Development Team"

LABEL maintainer="GeoNode development team"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8
WORKDIR /usr/src/geonode

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl \
    wget \
    unzip \
    gnupg2 \
    locales \
    netcat-openbsd \
    && sed -i -e 's/# C.UTF-8 UTF-8/C.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && apt-get autoremove --purge -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir -U pip setuptools wheel

COPY celery-cmd /usr/local/bin/celery-cmd
RUN chmod +x /usr/local/bin/celery-cmd

COPY . /usr/src/geonode/

# Cleanup apt update lists
# This is needed to reduce the size of the image, but it's better to move this RUN to geonode-base
RUN apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN chmod +x /usr/src/geonode/tasks.py /usr/src/geonode/entrypoint.sh

# Create specific log dir to geonode and statics and grant permissions to root group. 
# This is needed to avoid permission issues
RUN mkdir -p /var/log/geonode /mnt/volumes/statics && \
    chmod -R g=u /var/log/geonode /mnt/volumes/statics

RUN pip install --no-cache-dir -e .

EXPOSE 8000
