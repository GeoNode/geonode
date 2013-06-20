%define _tomcatdir /usr/share/tomcat
%define _datadir /usr/share
%define projname geoserver
Name:         %{projname}-tomcat
License:      GPL
Group:        Productivity/Scientific/Other
Summary:      Java based GIS server
Version:      2.3.0
Release:      1
URL:          http://geoserver.org
BuildRoot:    %{_tmppath}/%{name}-%{version}
Source0:      %{projname}-%{version}-war.zip
Source1:      geoserver_home.desktop
Source2:      geoserver_home.png
Provides:     %name-%{version}-%{release}
Conflicts:    geoserver
AutoReqProv:  0
BuildRequires:  fdupes
BuildRequires:  unzip
BuildRequires:  tomcat
BuildRequires: -post-build-checks
Requires:     java
Requires:     tomcat
Requires:     desktop-file-utils
BuildArch:    noarch

%description
GeoServer is an open source server written in Java that allows users to share and edit geospatial data.
Designed for interoperability, it publishes data from any major spatial data source using open standards. 
GeoServer has evolved to become an easy method of connecting existing information to Virtual Globes such as
Google Earth and NASA World Wind as well as web-based maps such as Google Maps and Windows Live Local. 
GeoServer is the reference implementation of the Open Geospatial Consortium Web Feature Service standard, 
and also implements the Web Map Service and Web Coverage Service specifications.


%prep
%setup -q -c -n %{projname}-%{version}-war


%build


%install
install -d $RPM_BUILD_ROOT%{_datadir}/applications
install -m 644 %SOURCE1  $RPM_BUILD_ROOT%{_datadir}/applications/geoserver_home.desktop
install -d  $RPM_BUILD_ROOT%{_tomcatdir}/webapps
install -d $RPM_BUILD_ROOT%{_datadir}/icons
install -m 644 %SOURCE2  $RPM_BUILD_ROOT%{_datadir}/icons/geoserver_home.png
cp geoserver.war -R -f  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/

%fdupes -s %{buildroot}

%post
# Back up tomcat config file before changing it
cp /etc/tomcat/tomcat.conf /etc/tomcat/tomcat.conf.orig.geoserver
JVM_OPTS='JAVA_OPTS="-Djava.awt.headless=true -Xms256m -Xmx768m -Xrs -XX:PerfDataSamplingInterval=500 -XX:MaxPermSize=128m"'

# Append a line with the new jvm configuration
if [ "$(grep ^GEOSERVER /etc/tomcat/tomcat.conf)" == "" ]; then
    echo '# GEOSERVER additions' >> /etc/tomcat/tomcat.conf
    #echo 'JAVA_HOME=/usr/' >> /usr/share/tomcat6/conf/tomcat6.conf
    echo $JVM_OPTS >> /etc/tomcat/tomcat.conf
fi

service tomcat restart

%postun
rm /etc/tomcat/tomcat.conf
cp /etc/tomcat/tomcat.conf.orig.geoserver /etc/tomcat/tomcat.conf
#rm -rf /usr/share/tomcat/webapps/geoserver 
service tomcat restart 

%clean
rm -rf %{buildroot}

%files
%defattr(644,root,root,755)
%{_datadir}/applications/geoserver_home.desktop
%{_datadir}/icons/*.png
%{_tomcatdir}/webapps/*.war

%changelog
