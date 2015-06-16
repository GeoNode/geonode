Name: geonode
Version: 1.1
Release: rc1.pre
Summary: Allows the creation, sharing, and collaborative use of geospatial data.
License: see /usr/share/doc/geonode/copyright
Distribution: Debian
Group: Converted/science
Requires(post): bash
Requires(preun): bash
Requires: python26, tomcat5, httpd, python26-virtualenv, python26-mod_wsgi, java-1.6.0-openjdk, postgresql84, postgresql84-server, postgresql84-python, postgresql84-libs, geos, postgresql84-devel, python26-devel, gcc
Conflicts: mod_python

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm

# repacking jar files takes a long time so we disable it
# %define __jar_repack %{nil} # this option doesn't seem to work on CentOS 5
%define __os_install_post \
    /usr/lib/rpm/redhat/brp-compress  \
    %{!?__debug_package:/usr/lib/rpm/redhat/brp-strip %{__strip}}; \
    /usr/lib/rpm/redhat/brp-strip-static-archive %{__strip}; \
    /usr/lib/rpm/redhat/brp-strip-comment-note %{__strip} %{__objdump}; \
    /usr/lib/rpm/brp-python-bytecompile;

%description
At its core, the GeoNode has a stack based on GeoServer, pycsw,
Django, and GeoExt that provides a platform for sophisticated
web browser spatial visualization and analysis. Atop this stack,
the project has built a map composer and viewer, tools for
analysis, and reporting tools.


%install
	rm -rf $RPM_BUILD_ROOT
	mkdir -p $RPM_BUILD_ROOT/usr/share/geonode
        # RELEASE=GeoNode-%{version}-
	RELEASE=GeoNode-1.0.1-2011-08-23
        for f in bootstrap.py deploy.ini.ex deploy-libs.txt geonode-webapp.pybundle pavement.py README.rst
        do
            cp "$RELEASE/$f" "$RPM_BUILD_ROOT"/usr/share/geonode/
        done
	cp -rp scripts/* $RPM_BUILD_ROOT/usr/share/geonode/.

        #Deploy Java webapps (WAR files)
        TC="$RPM_BUILD_ROOT"/var/lib/tomcat5/webapps/
        GS_DATA="$RPM_BUILD_ROOT"/var/lib/geonode-geoserver-data/
        mkdir -p "$TC"
        unzip -qq $RELEASE/geoserver.war -d $TC/geoserver/
        cp -R "$TC"/geoserver/data/ "$GS_DATA"
        (cd "$TC"/geoserver/WEB-INF/ && patch -p0) < geoserver.patch
        unzip -qq $RELEASE/geonetwork.war -d $TC/geonetwork/

        #Put Apache config files in place
        mkdir -p "$RPM_BUILD_ROOT"/etc/httpd/conf.d/ \
                 "$RPM_BUILD_ROOT"/var/www/geonode/wsgi/ \
                 "$RPM_BUILD_ROOT"/etc/geonode/

        cp geonode.conf "$RPM_BUILD_ROOT"/etc/httpd/conf.d/
        cp geonode.wsgi "$RPM_BUILD_ROOT"/var/www/geonode/wsgi/
        cp local_settings.py "$RPM_BUILD_ROOT"/etc/geonode/

        #Set up virtualenv
	mkdir -p "$RPM_BUILD_ROOT"/var/www/geonode/{htdocs,htdocs/media,wsgi/geonode/}
        for f in bootstrap.py geonode-webapp.pybundle pavement.py 
        do
            cp "$RELEASE"/$f "$RPM_BUILD_ROOT"/var/www/geonode/wsgi/geonode/
        done
        cp deps/psycopg2-2.4.2.tar.gz "$RPM_BUILD_ROOT"/var/www/geonode/wsgi/geonode
%post

cat << EOF >> /etc/sysconfig/tomcat5
# Next line added for GeoNode services
JAVA_OPTS="-Xmx1024m -XX:MaxPermSize=256m -XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement"
EOF

pushd /var/www/geonode/wsgi/geonode/
    python26 bootstrap.py
    bin/pip install psycopg2-2.4.2.tar.gz
popd

ln -s /etc/geonode/local_settings.py /var/www/geonode/wsgi/geonode/src/GeoNodePy/geonode/local_settings.py

echo "GEONODE: you will need to run /usr/share/geonode/setup.sh to complete this installation"

%preun

%postun

%clean

%files
%defattr(-,root,root,-)
%dir /usr/share/geonode/*
%dir /var/www/geonode/
%config /etc/geonode/local_settings.*
%config /etc/httpd/conf.d/geonode.conf
%config /var/www/geonode/wsgi/geonode.wsgi
%config /var/lib/tomcat5/webapps/*/WEB-INF/web.xml
/var/www/geonode/wsgi/geonode/*
%attr(-,tomcat,tomcat) %config %dir /var/lib/geonode-geoserver-data
%attr(-,tomcat,tomcat) %config /var/lib/geonode-geoserver-data/*
%dir /var/lib/tomcat5/webapps/geoserver
/var/lib/tomcat5/webapps/geoserver/*
%attr(-,tomcat,tomcat) %dir /var/lib/tomcat5/webapps/geonetwork
%attr(-,tomcat,tomcat) /var/lib/tomcat5/webapps/geonetwork/*
