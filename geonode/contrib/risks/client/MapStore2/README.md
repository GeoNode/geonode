[![Stories in Ready](https://badge.waffle.io/geosolutions-it/MapStore2.png?label=ready&title=Ready)](https://waffle.io/geosolutions-it/MapStore2)
[![Build Status](https://travis-ci.org/geosolutions-it/MapStore2.svg?branch=master)](https://travis-ci.org/geosolutions-it/MapStore2)
[![Coverage Status](https://coveralls.io/repos/geosolutions-it/MapStore2/badge.svg?branch=master&service=github)](https://coveralls.io/github/geosolutions-it/MapStore2?branch=master)
[![Codacy Badge](https://www.codacy.com/project/badge/1648d484427346e2877006dc287379b6)](https://www.codacy.com/app/simone-giannecchini/MapStore2)
[![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/fold_left.svg?style=social&label=Follow%20%40mapstore2)](https://twitter.com/mapstore2)

MapStore 2
==========
MapStore 2 is a framework to build *web mapping* applications using standard mapping libraries, such as [OpenLayers 3](http://openlayers.org/) and [Leaflet](http://leafletjs.com/).

MapStore 2 has several example applications:
 * MapViewer is a simple viewer of preconfigured maps (optionally stored in a database using GeoStore)
 * MapPublisher has been developed to create, save and share in a simple and intuitive way maps and mashups created selecting contents by server like OpenStreetMap, Google Maps, MapQuest or specific servers provided by your organization or third party.
 
For more information check the [MapStore documentation](https://dev.mapstore2.geo-solutions.it/mapstore/docs/).

Download
------------
You can download the WAR file from the the latest release [here](https://github.com/geosolutions-it/MapStore2/releases/latest).

[All the releases](https://github.com/geosolutions-it/MapStore2/releases)

Quick Start
------------
After downloading the MapStore2 war file, install it in your java web container (e.g. Tomcat), with usual procedures for the container (normally you only need to copy the war file in the webapps subfolder).

If you don't have a java web container you can download Apache Tomcat from [here](https://tomcat.apache.org/download-70.cgi) and install it. You will also need a Java7 [JRE](http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html)

Then you can access MapStore2 using the following URL (assuming the web container is on the standard 8080 port):

[http://localhost:8080/mapstore](http://localhost:8080/mapstore)

Use the default credentials (admin / admin) to login and start creating your maps!

Documentation
-------------
You can find more documentaion about how to build, install or develop with MapStore 2 on the [documentation site](https://dev.mapstore2.geo-solutions.it/mapstore/docs/).

License
------------
MapStore 2 is Free and Open Source software, it is based on OpenLayers 3, Leaflet and [ReactJS](https://facebook.github.io/react/), and is licensed under the Simplified BSD License.


Demo Instances
---------------
We have the following instances:

1. a DEV instance, which can be accessed [here](http://dev.mapstore2.geo-solutions.it), where all the changes are deployed once they are published on the Master branch of our repo
2. a QA instance, which can be accessed  [here](http://qa.mapstore2.geo-solutions.it), that becomes active 1 week before any release, during the hardening phase, and deploys the release branch whenever a fix is pushed onto it.
3. a STABLE instance, which can be accessed [here](http://mapstore2.geo-solutions.it), that gets deployed on demand after each release.

As a user you need to be aware of STABLE and DEV, QA is used internally before a release; for 1 Week it will diverge from STABLE as it is actually anticipating the next stable.
So, if you want to test latest features use DEV, if you are not that brave use STABLE. You might forget that QA exists unless you are parte of the developers team.

Start developing your custom app
------------

Clone the repository with the --recursive option to automatically clone submodules:

`git clone --recursive https://github.com/geosolutions-it/MapStore2.git`

Install NodeJS >= 4.6.1 , if needed, from [here](https://nodejs.org/en/download/releases/).

Update npm to 3.x, using:

`npm install -g npm@3`

Start the demo locally:

`npm cache clean` (this is useful to prevent errors on Windows during install)

`npm install`

`npm start`

The demo runs at `http://localhost:8081` afterwards.

Install latest Maven, if needed, from [here](https://maven.apache.org/download.cgi) (version 3.1.0 is required).

Build the deployable war:

`./build.sh`

Deploy the generated mapstore.war file (in web/target) to your favourite J2EE container (e.g. Tomcat).

Read more on the [documentation site](https://dev.mapstore2.geo-solutions.it/mapstore/docs/).

Professional Support
---------------------
MapStore 2 is being developed by [GeoSolutions](http://www.geo-solutions.it/) hence you can talk to us for professional support. Anyway the project is a real Open Source project hence you can contribute to it (see section below).

Communication
---------------------
We currently have two mailing list, [one](https://groups.google.com/d/forum/mapstore-users) for users and [one](https://groups.google.com/d/forum/mapstore-developers) for developers. The first one is for those who are willing to use MapStore and need help/directions, the latter is for those trying to extend/proposed fixes for MapStore.


Contributing
---------------------
We welcome contributions in any form:

* pull requests for new features
* pull requests for bug fixes
* pull requests for documentation
* funding for any combination of the above

For more information check [this](https://github.com/geosolutions-it/MapStore2/blob/master/CONTRIBUTING.md) page.
