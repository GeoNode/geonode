CentOS packaging scripts for GeoNode
====================================

This repository contains the scripts used to build the .rpm (CentOS) package
for GeoNode.  If you are interested in modifying GeoNode itself you may find
http://github.com/GeoNode/geonode more relevant.

Building
--------

To produce a .rpm package which can be redistributed:

* Install the rpm packaging tools::

    yum install rpmbuild rpm-devtools

* Run the rpmdev-setuptree tool to set up your user account for building RPMs::

    rpmdev-setuptree

* Point the BUILD and SPECS subdirectories of the RPM build tree at your
  checkout of this project::

    rmdir ~/rpmbuild/{BUILD,SPECS} &&
    ln -s ~/geonode-rpm/{BUILD,SPECS} ~/rpmbuild/

* Acquire a GeoNode tar.gz archive (by either building it from sources, or from
  http://dev.geonode.org/release/ ) and unpack it into
  :file:`geonode-rpm/BUILD/`.

* Fetch the psycopg2 sources from http://initd.org/psycopg/download/ and place
  the tarball in :file:`geonode-rpm/BUILD/deps`.

* You should now have a directory structure like so::

    geonode-rpm/
      + BUILD/
        + GeoNode-{version}/
        + deps/
          - psycopg2-2.3.1.tar.gz
        + scripts/
      + SPECS/
        - geonode.spec
        - opengeo.repo

* Now you can build the GeoNode RPM by using the ``rpmbuild`` command::

    rpmbuild -bb ~/rpmbuild/SPECS/geonode.spec

.. note::

    Currently, building on CentOS machines requires specifying the --buildroot
    option to rpmbuild, like so::

        rpmbuild -bb ~/rpmbuild/SPECS/geonode.spec \
          --buildroot=/home/rpmbuild/rpmbuild/BUILDROOT/

After running ``rpmbuild`` you should have the RPM package one directory level
in the :file:`rpmbuild` directory.

Installation
------------

As described in the GeoNode manual, you can access OpenGeo's YUM repository to
get pre-built GeoNode packages.  However, if you want to build a package and
install that instead, you can avoid the need for a repository of your own by
using the following command::

    yum localinstall geonode-{version}.rpm --nogpgcheck

As GeoNode depends on software not provided by the main CentOS distribution,
you will still need to enable some third-party repositories.  OpenGeo's
repository will mirror all GeoNode dependencies, or you can use
`EPEL<http://fedoraproject.org/wiki/EPEL>`_ and
`ELGIS<http://wiki.osgeo.org/wiki/Enterprise_Linux_GIS>`_ together.
