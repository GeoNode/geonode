ARG BASE_IMAGE_VERSION
#FROM 52north/geonode_thuenen:${BASE_IMAGE_VERSION}
FROM 52north/geonode_thuenen:4.x

# geonode-project installs ldap per default
# there the locale is set explicitly
# see https://github.com/GeoNode/geonode-project/blob/master/Dockerfile#L8C1-L11C17
RUN sed -i -e 's/# C.UTF-8 UTF-8/C.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY ./geonode-mapstore-client /usr/src/django_geonode_mapstore_client_dev
RUN yes w | pip install -e /usr/src/django_geonode_mapstore_client_dev

COPY ./requirements.txt /usr/src/more_requirements.txt
RUN yes w | pip install --src /usr/src -r /usr/src/more_requirements.txt

RUN rm .env*
