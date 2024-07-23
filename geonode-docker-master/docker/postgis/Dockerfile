FROM postgis/postgis:15-3.3-alpine
LABEL GeoNode development team

COPY ./initdb-geonode.sh /docker-entrypoint-initdb.d/geonode.sh
RUN chmod +x /docker-entrypoint-initdb.d/geonode.sh
