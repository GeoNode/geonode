FROM alpine:latest
LABEL GeoNode development team

# Install curl in alpine 3.3+
RUN apk --no-cache add curl

# Download required files
RUN mkdir -p /tmp/geonode/downloaded
ENV TEMP_DOWNLOADED /tmp/geonode/downloaded
WORKDIR ${TEMP_DOWNLOADED}

ENV GEOSERVER_VERSION=2.24.4

# ADD download.sh ${TEMP_DOWNLOADED}
# RUN chmod +x ${TEMP_DOWNLOADED}/download.sh
# RUN ${TEMP_DOWNLOADED}/download.sh $GEOSERVER_VERSION $TEMP_DOWNLOADED
# we added below block for tosca
COPY geoserver-data-tosca.zip .
RUN unzip -x -d . ./geoserver-data-tosca.zip

# for debugging
RUN ls -lart

# Preparing the volume
ENV BASE_GEOSERVER_DATA_DIR /geoserver_data
RUN mkdir -p ${BASE_GEOSERVER_DATA_DIR}
RUN cp -r ${TEMP_DOWNLOADED}/data ${BASE_GEOSERVER_DATA_DIR}

# Clean up temporary files and directories
RUN rm -rf /tmp/geonode/

# Define the volume
VOLUME ${BASE_GEOSERVER_DATA_DIR}/data
