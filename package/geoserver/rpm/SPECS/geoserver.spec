Name: geonode
Version: 2.0
Release: alpha1
Summary: Allows the creation, sharing, and collaborative use of geospatial data.
License: see /usr/share/doc/geonode/copyright
Distribution: Debian
Group: Converted/science
Requires(post): bash
Requires(preun): bash
Conflicts: mod_python

#%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm

# repacking jar files takes a long time so we disable it
%define __jar_repack %{nil}

%description
At its core, the GeoNode has a stack based on GeoServer, pycsw,
Django, and GeoExt that provides a platform for sophisticated
web browser spatial visualization and analysis. Atop this stack,
the project has built a map composer and viewer, tools for
analysis, and reporting tools.

%build
pushd $GEONODE_EXT_ROOT
mvn clean install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/share/geonode/geoserver
unzip -d $RPM_BUILD_ROOT/usr/share/geonode/geoserver target/geoserver.war
mkdir -p $RPM_BUILD_ROOT/etc/tomcat6/Catalina/localhost/
echo '<Context path="/geoserver" docBase="/usr/share/geonode/geoserver/" />'  >> $RPM_BUILD_ROOT/etc/tomcat6/Catalina/localhost/geoserver.xml
mkdir -p $RPM_BUILD_ROOT/usr/share/opengeo-suite/geoserver/WEB-INF/lib/
cp target/geonode-geoserver-ext-0.3.jar $RPM_BUILD_ROOT/usr/share/opengeo-suite/geoserver/WEB-INF/lib/

# GeoServer
%package geoserver
Summary: GeoServer for %{name}.
Group: Development/Libraries
Requires: tomcat6

%description geoserver
High performance, standards-compliant map and geospatial data server.
GeoServer is an open source software server written in Java that allows users to share 
and edit geospatial data. Contains GeoNode extensions.

%files geoserver
%defattr(-, root, root, 0755)
/usr/share/geonode/*
/etc/tomcat6/Catalina/localhost/geoserver.xml

%post geoserver
# Back up tomcat6 config file before changing it
cp /usr/share/tomcat6/conf/tomcat6.conf /usr/share/tomcat6/conf/tomcat6.conf.orig

#GeoServer needs more ram than the default for tomcat.
JVM_OPTS='JAVA_OPTS="-Djava.awt.headless=true -Xms256m -Xmx768m -Xrs -XX:PerfDataSamplingInterval=500 -XX:MaxPermSize=128m -DGEOSERVER_CSRF_DISABLED=true"'

# Append a line with the new jvm configuration
if [ "$(grep ^GEOSERVER /usr/share/tomcat6/conf/tomcat6.conf)" == "" ]; then 
	echo '# GEOSERVER additions' >> /usr/share/tomcat6/conf/tomcat6.conf
	echo 'JAVA_HOME=/usr/' >> /usr/share/tomcat6/conf/tomcat6.conf
	echo $JVM_OPTS >> /usr/share/tomcat6/conf/tomcat6.conf
fi

# Fix permissions on deployed jar
chown -R tomcat:tomcat /usr/share/geonode/geoserver/

# start tomcat after installing geoserver
service tomcat6 restart

%postun geoserver
service tomcat6 restart

# OpenGeo Suite GeoServer
%package opengeo-geoserver
Summary:  %{name} extensions for the OpenGeo Suite.
Group: Development/Libraries
Requires: opengeo-geoserver

%description opengeo-geoserver
GeoNode extensions for The OpenGeo Suite.

%files opengeo-geoserver
%defattr(-, root, root, 0755)
/usr/share/opengeo-suite/geoserver/WEB-INF/lib/*

%post opengeo-geoserver
service tomcat6 restart

%postun opengeo-geoserver
service tomcat6 restart
