ARG IMAGE_VERSION=9.0-jdk11-openjdk-slim-bullseye
ARG JAVA_HOME=/usr/local/openjdk-11
FROM tomcat:$IMAGE_VERSION
LABEL GeoNode Development Team

ARG GEOSERVER_CORS_ENABLED=False
ARG GEOSERVER_CORS_ALLOWED_ORIGINS=*
ARG GEOSERVER_CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,HEAD,OPTIONS
ARG GEOSERVER_CORS_ALLOWED_HEADERS=*
#
# Set GeoServer version and data directory
#
ENV GEOSERVER_VERSION=2.23.0
ENV GEOSERVER_DATA_DIR="/geoserver_data/data"
ENV GEOSERVER_CORS_ENABLED=$GEOSERVER_CORS_ENABLED
ENV GEOSERVER_CORS_ALLOWED_ORIGINS=$GEOSERVER_CORS_ALLOWED_ORIGINS
ENV GEOSERVER_CORS_ALLOWED_METHODS=$GEOSERVER_CORS_ALLOWED_METHODS
ENV GEOSERVER_CORS_ALLOWED_HEADERS=$GEOSERVER_CORS_ALLOWED_HEADERS
#
# Download and install GeoServer
#
RUN apt-get update -y && apt-get install curl wget unzip -y
RUN cd /usr/local/tomcat/webapps \
    && wget --no-check-certificate --progress=bar:force:noscroll https://artifacts.geonode.org/geoserver/${GEOSERVER_VERSION}/geoserver.war -O geoserver.war \
    && unzip -q geoserver.war -d geoserver \
    && rm geoserver.war \
    && mkdir -p $GEOSERVER_DATA_DIR

VOLUME $GEOSERVER_DATA_DIR

# added by simonelanucara https://github.com/simonelanucara
# Optionally add JAI, ImageIO and Marlin Render for improved Geoserver performance
WORKDIR /tmp

RUN wget --no-check-certificate https://repo1.maven.org/maven2/org/postgis/postgis-jdbc/1.3.3/postgis-jdbc-1.3.3.jar -O postgis-jdbc-1.3.3.jar && \
    wget --no-check-certificate https://maven.geo-solutions.it/org/hibernatespatial/hibernate-spatial-postgis/1.1.3.2/hibernate-spatial-postgis-1.1.3.2.jar -O hibernate-spatial-postgis-1.1.3.2.jar && \
    rm /usr/local/tomcat/webapps/geoserver/WEB-INF/lib/hibernate-spatial-h2-geodb-1.1.3.2.jar && \
    mv hibernate-spatial-postgis-1.1.3.2.jar /usr/local/tomcat/webapps/geoserver/WEB-INF/lib/ && \
    mv postgis-jdbc-1.3.3.jar /usr/local/tomcat/webapps/geoserver/WEB-INF/lib/

###########docker host###############
# Set DOCKERHOST variable if DOCKER_HOST exists
ARG DOCKERHOST=${DOCKERHOST}
# for debugging
RUN echo -n #1===>DOCKERHOST=${DOCKERHOST}
#
ENV DOCKERHOST ${DOCKERHOST}
# for debugging
RUN echo -n #2===>DOCKERHOST=${DOCKERHOST}

###########docker host ip#############
# Set GEONODE_HOST_IP address if it exists
ARG GEONODE_HOST_IP=${GEONODE_HOST_IP}
# for debugging
RUN echo -n #1===>GEONODE_HOST_IP=${GEONODE_HOST_IP}
#
ENV GEONODE_HOST_IP ${GEONODE_HOST_IP}
# for debugging
RUN echo -n #2===>GEONODE_HOST_IP=${GEONODE_HOST_IP}
# If empty set DOCKER_HOST_IP to GEONODE_HOST_IP
ENV DOCKER_HOST_IP=${DOCKER_HOST_IP:-${GEONODE_HOST_IP}}
# for debugging
RUN echo -n #1===>DOCKER_HOST_IP=${DOCKER_HOST_IP}
# Trying to set the value of DOCKER_HOST_IP from DOCKER_HOST
RUN if ! [ -z ${DOCKER_HOST_IP} ]; \
    then echo export DOCKER_HOST_IP=${DOCKERHOST} | \
    sed 's/tcp:\/\/\([^:]*\).*/\1/' >> /root/.bashrc; \
    else echo "DOCKER_HOST_IP is already set!"; fi
# for debugging
RUN echo -n #2===>DOCKER_HOST_IP=${DOCKER_HOST_IP}

# Set WEBSERVER public port
ARG PUBLIC_PORT=${PUBLIC_PORT}
# for debugging
RUN echo -n #1===>PUBLIC_PORT=${PUBLIC_PORT}
#
ENV PUBLIC_PORT=${PUBLIC_PORT}
# for debugging
RUN echo -n #2===>PUBLIC_PORT=${PUBLIC_PORT}

# set nginx base url for geoserver
RUN echo export NGINX_BASE_URL=http://${NGINX_HOST}:${NGINX_PORT}/ | \
    sed 's/tcp:\/\/\([^:]*\).*/\1/' >> /root/.bashrc

# copy the script and perform the run of scripts from entrypoint.sh
RUN mkdir -p /usr/local/tomcat/tmp
WORKDIR /usr/local/tomcat/tmp
COPY set_geoserver_auth.sh /usr/local/tomcat/tmp
COPY setup_auth.sh /usr/local/tomcat/tmp
COPY requirements.txt /usr/local/tomcat/tmp
COPY get_dockerhost_ip.py /usr/local/tomcat/tmp
COPY get_nginxhost_ip.py /usr/local/tomcat/tmp
COPY entrypoint.sh /usr/local/tomcat/tmp
COPY ./templates /templates
COPY multidump.sh /usr/local/tomcat/tmp
COPY multidump-alt.sh /usr/local/tomcat/tmp

RUN apt-get update \
    && apt-get install -y procps less \
    && apt-get install -y python3 python3-pip python3-dev \
    && chmod +x /usr/local/tomcat/tmp/set_geoserver_auth.sh \
    && chmod +x /usr/local/tomcat/tmp/setup_auth.sh \
    && chmod +x /usr/local/tomcat/tmp/entrypoint.sh \
    && pip3 install pip --upgrade \
    && pip3 install -r requirements.txt \
    && chmod +x /usr/local/tomcat/tmp/get_dockerhost_ip.py \
    && chmod +x /usr/local/tomcat/tmp/get_nginxhost_ip.py

RUN pip install j2cli

ENV JAVA_OPTS="-Djava.awt.headless=true -Dgwc.context.suffix=gwc -XX:+UnlockDiagnosticVMOptions -XX:+LogVMOutput -XX:LogFile=/var/log/jvm.log -XX:MaxPermSize=512m -XX:PermSize=256m -Xms512m -Xmx2048m -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=4 -Dfile.encoding=UTF8 -Djavax.servlet.request.encoding=UTF-8 -Djavax.servlet.response.encoding=UTF-8 -Duser.timezone=GMT -Dorg.geotools.shapefile.datetime=false -DGS-SHAPEFILE-CHARSET=UTF-8 -DGEOSERVER_CSRF_DISABLED=true -DPRINT_BASE_URL=http://geoserver:8080/geoserver/pdf -Xbootclasspath/a:/usr/local/tomcat/webapps/geoserver/WEB-INF/lib/marlin-0.9.3.jar -Dsun.java2d.renderer=org.marlin.pisces.MarlinRenderingEngine"

CMD ["/usr/local/tomcat/tmp/entrypoint.sh"]