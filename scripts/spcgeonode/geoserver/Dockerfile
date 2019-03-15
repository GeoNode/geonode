FROM openjdk:8-jre-alpine

ARG version=2.14.2
ARG branch=2.14.x
ARG plugins=

# Install dependencies
RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
        ca-certificates \
    && update-ca-certificates 2>/dev/null || true
RUN apk add openssl wget curl postgresql-client fontconfig ttf-ubuntu-font-family

WORKDIR /

# Download Geoserver
# we first download vanilla geoserver, as it comes with preset jetty and launch scripts
# then we replace it with the geonode build
# TODO : this is a bit dirty..... can't we stat from vanilla Geoserver ?
# TODO : merge into on step
RUN echo "Download geoserver $version for geonode" && \
    while [ 1 ]; do \
      wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 0 --continue https://downloads.sourceforge.net/project/geoserver/GeoServer/$version/geoserver-$version-bin.zip --secure-protocol=TLSv1 --no-check-certificate; \
      if [ $? = 0 ]; then break; fi; \
      sleep 1s; \
    done;
RUN wget https://build.geo-solutions.it/geonode/geoserver/latest/geoserver-$branch.war --no-check-certificate && \
    unzip geoserver-$version-bin.zip && \
    mv geoserver-$version geoserver && \
    rm /geoserver-$version-bin.zip && \
    rm /geoserver-$version/webapps/geoserver/* -rf && \
    unzip -o geoserver-$branch.war -d /geoserver/webapps/geoserver/ && \
    rm /geoserver-$branch.war

# Plugins support
# Example:
#   $ docker-compose build --build-arg plugins="csw" geoserver
RUN for plugin in $plugins; do \
        wget https://downloads.sourceforge.net/project/geoserver/GeoServer/$version/extensions/geoserver-$version-$plugin-plugin.zip && \
        unzip -o geoserver-$version-$plugin-plugin.zip -d /geoserver/webapps/geoserver/WEB-INF/lib && \
        rm geoserver-$version-$plugin-plugin.zip; \
    done

# Download initial data dir
RUN wget https://build.geo-solutions.it/geonode/geoserver/latest/data-$branch.zip --no-check-certificate
RUN unzip /data-$branch.zip
RUN ls /data

WORKDIR /geoserver/

# Add the entrypoint
ADD docker-entrypoint.sh /docker-entrypoint.sh 
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# Export ports
EXPOSE 8080

# Set environnment variables
ENV GEOSERVER_HOME=/geoserver
ENV GEOSERVER_DATA_DIR=/spcgeonode-geodatadir

# Run geoserver
CMD ["bin/startup.sh"]
