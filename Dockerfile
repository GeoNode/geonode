<<<<<<< HEAD
ARG GEONODE_BASE_IMAGE=geonode/geonode-base:latest-ubuntu-22.04
FROM ${GEONODE_BASE_IMAGE}

ARG GEONODE_VERSION=master

# Some label best practices
# https://www.docker.com/blog/docker-best-practices-using-tags-and-labels-to-manage-docker-image-sprawl/
LABEL org.opencontainers.image.title="GeoNode" \
    org.opencontainers.image.version=${GEONODE_VERSION} \
    org.opencontainers.image.vendor="GeoNode Development Team"
=======
FROM geonode/geonode-base:latest-ubuntu-26.04
>>>>>>> c125d8f2231ce7b1a80b165656084a8d99dc9637

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

<<<<<<< HEAD
RUN chmod +x \
        wait-for-databases.sh \
        tasks.py \
        entrypoint.sh \
        celery.sh \
        celery-cmd && \
    mv wait-for-databases.sh /usr/local/bin/wait-for-databases && \
    mv celery.sh /usr/local/bin/celery-commands && \
    mv celery-cmd /usr/local/bin/celery-cmd 
=======
RUN python -m pip install --no-cache-dir -U pip setuptools wheel

COPY celery-cmd /usr/bin/celery-cmd
RUN chmod +x /usr/bin/celery-cmd
>>>>>>> c125d8f2231ce7b1a80b165656084a8d99dc9637

COPY . /usr/src/geonode/

<<<<<<< HEAD
RUN yes w | pip install --no-cache --src /usr/src -r requirements.txt &&\
    yes w | pip install --no-cache -e .

# Cleanup apt update lists
# This is needed to reduce the size of the image, but it's better to move this RUN to geonode-base
RUN apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create specific log dir to geonode and statics and grant permissions to root group. 
# This is needed to avoid permission issues
RUN mkdir -p /var/log/geonode /mnt/volumes/statics && \
    chmod -R g=u /var/log/geonode /mnt/volumes/statics

# Export ports
EXPOSE 8000

# We provide no command as this image can be used to serve the django project or run celery tasks
ENTRYPOINT [ ./entrypoint.sh ]

=======
RUN chmod +x /usr/src/geonode/tasks.py /usr/src/geonode/entrypoint.sh

RUN pip install --no-cache-dir -e .

EXPOSE 8000
>>>>>>> c125d8f2231ce7b1a80b165656084a8d99dc9637
