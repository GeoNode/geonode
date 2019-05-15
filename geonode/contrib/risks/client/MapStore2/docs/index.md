


![MapStore Logo](https://github.com/geosolutions-it/MapStore2/blob/master/MapStore2.png?raw=true)

**[MapStore](http://mapstore2.geo-solutions.it/)** is a framework to build _web mapping_ applications using standard mapping libraries, such as _OpenLayers 3_ and _Leaflet_.

MapStore has several example applications:

 * **[MapViewer / Composer](http://mapstore2.geo-solutions.it/mapstore/)** is a simple viewer of preconfigured maps (optionally stored in a database using GeoStore), and a composer of your own maps.
 * **[The Playground](http://dev.mapstore2.geo-solutions.it/mapstore/examples/plugins/)** a tool to built a custom UI using the framework plugins


MapStore 2 is based on OpenLayers 3, Leaflet and ReactJS, and is licensed under the GPLv3 license.

[![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/fold_left.svg?style=social&label=Follow%20%40mapstore2)](https://twitter.com/mapstore2)


Quick Start
-----------

You can either choose to download a standalone *binary package* or a *WAR file* to quickly start playing with MapStore2.

Binary package
--------------
Download the binary package file from the the latest release [here](https://github.com/geosolutions-it/MapStore2/releases/latest).

Go to the location where you saved the zip file, unzip the contents and run:

Windows: `mapstore2_startup.bat`

Linux: `./mapstore2_startup.sh`

Point you browser to: [http://localhost:8082/mapstore](http://localhost:8082/mapstore)

To stop MapStore2 simply do:

Windows: `mapstore2_shutdown.bat`

Linux: `./mapstore2_shutdown.sh`


WAR file
--------
Download the WAR file from the the latest release [here](https://github.com/geosolutions-it/MapStore2/releases/latest).

[All the releases](https://github.com/geosolutions-it/MapStore2/releases)

After downloading the MapStore2 war file, install it in your java web container (e.g. Tomcat), with usual procedures for the container (normally you only need to copy the war file in the webapps subfolder).

If you don't have a java web container you can download Apache Tomcat from [here](https://tomcat.apache.org/download-70.cgi) and install it. You will also need a Java7 [JRE](http://www.oracle.com/technetwork/java/javase/downloads/jre7-downloads-1880261.html)

Then you can access MapStore2 using the following URL (assuming the web container is on the standard 8080 port):

[http://localhost:8080/mapstore](http://localhost:8080/mapstore)

Use the default credentials (admin / admin) to login and start creating your maps!

# Documentation
 * [Developers Guide](developer-guide/)
 * [Users Guide] TBD
