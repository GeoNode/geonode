FROM geonode/django
MAINTAINER GeoNode development team

# Set DOCKER_HOST address
ARG DOCKER_HOST=${DOCKER_HOST}
# for debugging
RUN echo -n DOCKER_HOST=$DOCKER_HOST
#
ENV DOCKER_HOST ${DOCKER_HOST}
# for debugging
RUN echo -n DOCKER_HOST=$DOCKER_HOST

ENV DOCKER_HOST_IP ${DOCKER_HOST_IP}
RUN echo export DOCKER_HOST_IP=${DOCKER_HOST} | sed 's/tcp:\/\/\([^:]*\).*/\1/' >> /root/.bashrc