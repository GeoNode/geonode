.. _standards:

Standards
=========

GeoNode is based on a set of Open Geospatial Consortium (OGC) standards. These standards enable GeoNode installations to be interoperable with a wide variety of tools that support these OGC standards and enable federation with other OGC compliant services and infrastructure. Reference links about these standards are also included at the end of this module.

GeoNode is also based on Web Standards ...

Open Geospatial Consortium (OGC) Standards
------------------------------------------

Web Map Service (WMS)
~~~~~~~~~~~~~~~~~~~~~

The Web Map Service (WMS) specification defines an interface for requesting rendered map images across the web. It is used within GeoNode to display maps in the pages of the site and in the GeoExplorer application to display rendered layers based on default or custom styles.

Web Feature Service (WFS)
~~~~~~~~~~~~~~~~~~~~~~~~~

The Web Feature Service (WFS) specification defines an interface for reading and writing geographic features across the web. It is used within GeoNode to enable downloading of vector layers in various formats and within GeoExplorer to enable editing of Vector Layers that are stored in a GeoNode.

Web Coverage Service (WCS)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Web Coverage Service (WCS) specification defines an interface for reading and writing geospatial raster data as "coverages" across the web. It is used within GeoNode to enable downloading of raster layers in various formats.

Catalogue Service for Web (CSW)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Catalogue Service for Web (CSW) specification defines an interface for exposing a catalogue of geospatial metadata across the web. It is used within GeoNode to enable any application to search GeoNode's catalogue or to provide federated search that includes a set of GeoNode layers within another application.

Tile Mapping Service (TMS/WMTS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Tile Mapping Service (TMS) specification defines and interface for retrieving rendered map tiles over the web. It is used within geonode to enable serving of a cache of rendered layers to be included in GeoNode's web pages or within the GeoExplorer mapping application. Its purpose is to improve performance on the client vs asking the WMS for rendered images directly.

Web Standards
-------------

HTML
~~~~

CSS
~~~

REST
~~~~ 
