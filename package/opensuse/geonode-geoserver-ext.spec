%define _tomcatdir /usr/share/tomcat
%define _datadir /usr/share
Name:         geonode-geoserver-ext
License:      GPL-2.0
Group:        Productivity/Scientific/Other
Summary:      GeoNode plug-in for GeoServer
Version:      0.3
Release:      1
URL:          http://geonode.org/
BuildRoot:    %{_tmppath}/%{name}-%{version}
Source0:      %{name}-%{version}-geoserver-plugin.zip
Provides:     %{name}-%{version}-%{release}
AutoReqProv:  0
BuildRequires:  fdupes
BuildRequires:  unzip
BuildRequires:  tomcat
BuildRequires: -post-build-checks
Requires:     java
Requires:     tomcat
Requires:     geoserver-tomcat
Requires:     desktop-file-utils
BuildArch:    noarch

%description
GeoNode is a platform for the management and publication of geospatial data. 
It brings together mature and stable open-source software projects under a 
consistent and easy-to-use interface allowing users, with little training, 
to quickly and easily share data and create interactive maps. GeoNode provides 
a cost-effective and scalable tool for developing information management systems.


%prep
%setup -q -c -n %{name}-%{version}


%build


%install
install -d  $RPM_BUILD_ROOT%{_tomcatdir}/webapps
install -d  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/geoserver
install -d  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/geoserver/WEB-INF
install -d  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/geoserver/WEB-INF/lib
cp %{name}-%{version}.jar -R -f  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/geoserver/WEB-INF/lib/
cp gt-process-8.2.jar -R -f  $RPM_BUILD_ROOT%{_tomcatdir}/webapps/geoserver/WEB-INF/lib/

%fdupes -s %{buildroot}

%post
service tomcat restart

%postun
service tomcat restart 

%clean
rm -rf %{buildroot}

%files
%defattr(644,root,root,755)
%{_tomcatdir}/webapps/geoserver/WEB-INF/lib/*.jar

%changelog
