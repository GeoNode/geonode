FROM geonode/geonode-base:latest-ubuntu-26.04
LABEL GeoNode development team

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

COPY celery-cmd /usr/bin/celery-cmd
RUN chmod +x /usr/bin/celery-cmd

COPY . /usr/src/geonode/

RUN chmod +x /usr/src/geonode/tasks.py /usr/src/geonode/entrypoint.sh

RUN pip install --no-cache-dir -e .

EXPOSE 8000
