FROM java:9-jdk
MAINTAINER Wayner Barrios<wayner@piensa.co>
# Install Ant

ENV ANT_VERSION 1.9.4
RUN cd && \
    wget -q http://archive.apache.org/dist/ant/binaries/apache-ant-${ANT_VERSION}-bin.tar.gz && \
    tar -xzf apache-ant-${ANT_VERSION}-bin.tar.gz && \
    mv apache-ant-${ANT_VERSION} /opt/ant && \
    rm apache-ant-${ANT_VERSION}-bin.tar.gz

ENV ANT_HOME /opt/ant
#Adding ANT into bin
ENV PATH ${PATH}:/opt/ant/bin

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
EXPOSE 9090