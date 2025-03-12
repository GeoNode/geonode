ARG GEONODE_BASE_IMAGE=geonode/geonode-base:latest-ubuntu-22.04
FROM ${GEONODE_BASE_IMAGE}

ARG GEONODE_VERSION=master

# Some label best practices
# https://www.docker.com/blog/docker-best-practices-using-tags-and-labels-to-manage-docker-image-sprawl/
LABEL org.opencontainers.image.title="GeoNode" \
    org.opencontainers.image.version=${GEONODE_VERSION} \
    org.opencontainers.image.vendor="GeoNode Development Team"

# copy local geonode src inside container
COPY . /usr/src/geonode/
WORKDIR /usr/src/geonode

#COPY monitoring-cron /etc/cron.d/monitoring-cron
#RUN chmod 0644 /etc/cron.d/monitoring-cron
#RUN crontab /etc/cron.d/monitoring-cron
#RUN touch /var/log/cron.log
#RUN service cron start

RUN chmod +x \
        wait-for-databases.sh \
        tasks.py \
        entrypoint.sh \
        celery.sh \
        celery-cmd && \
    mv wait-for-databases.sh /usr/local/bin/wait-for-databases && \
    mv celery.sh /usr/local/bin/celery-commands && \
    mv celery-cmd /usr/local/bin/celery-cmd 

# # Install "geonode-contribs" apps
# RUN cd /usr/src; git clone https://github.com/GeoNode/geonode-contribs.git -b master
# # Install logstash and centralized dashboard dependencies
# RUN cd /usr/src/geonode-contribs/geonode-logstash; pip install --upgrade  -e . \
#     cd /usr/src/geonode-contribs/ldap; pip install --upgrade  -e .

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

