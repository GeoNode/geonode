Debian packaging scripts for GeoNode
====================================

This repository contains the scripts used to build the .deb (Ubuntu) package
for GeoNode.  If you are interested in modifying GeoNode itself you may find
http://github.com/GeoNode/geonode more relevant.

Building
--------

To produce a .deb package which can be redistributed:

* Install the debian packaging tools::

    apt-get install debhelper devscripts

* Acquire a GeoNode tar.gz archive (by either building it from sources, or from
  http://dev.geonode.org/release/ ) and unpack it, so that you have a
  directory structure like so::
 
    geonode-deb/
       + debian/
       + GeoNode-{version}

* Run the debuild tool to build the package::

    debuild -uc -us -A

* geonode-{version}.deb will be produced in the parent directory (one level
  above the directory where you cloned this project).

Installation
------------

As described in the GeoNode manual, you can access OpenGeo's APT repository to
get pre-built GeoNode packages.  However, if you want to build a package and
install that instead, you can avoid the need for a repository of your own by
using the following command::

    dpkg -i geonode-{version}.deb

If dpkg reports an error about unmet dependencies, you can issue the following
command to fetch dependencies and re-attempt the installation::

    apt-get install -f

