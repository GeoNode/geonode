FROM openjdk:8-jre-alpine

# Install dependencies
RUN apk add --no-cache ca-certificates openssl curl postgresql-client fontconfig ttf-ubuntu-font-family
RUN update-ca-certificates

WORKDIR /

# Download Geoserver
# we first download vanilla geoserver, as it comes with preset jetty and launch scripts
# then we replace it with the geonode build
# TODO : this is a bit dirty..... can't we stat from vanilla Geoserver ?
# TODO : merge into on step
RUN echo "Download geoserver for geonode" && \
    wget https://downloads.sourceforge.net/project/geoserver/GeoServer/2.14.0/geoserver-2.14.0-bin.zip && \
    wget https://build.geo-solutions.it/geonode/geoserver/latest/geoserver-2.14.x.war --no-check-certificate && \
    unzip geoserver-2.14.0-bin.zip && \
    rm /geoserver-2.14.0-bin.zip && \
    rm /geoserver-2.14.0/webapps/geoserver/* -rf && \
    unzip -o geoserver-2.14.x.war -d /geoserver-2.14.0/webapps/geoserver/ && \
    rm /geoserver-2.14.x.war

# Download initial data dir
RUN wget https://build.geo-solutions.it/geonode/geoserver/latest/data-2.14.x.zip --no-check-certificate
RUN unzip /data-2.14.x.zip
RUN ls /data

WORKDIR /geoserver-2.14.0/

# Add the entrypoint
ADD docker-entrypoint.sh /docker-entrypoint.sh 
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# Export ports
EXPOSE 8080

# Set environnment variables
ENV GEOSERVER_HOME=/geoserver-2.14.0
ENV GEOSERVER_DATA_DIR=/spcgeonode-geodatadir

# Run geoserver
CMD ["bin/startup.sh"]
