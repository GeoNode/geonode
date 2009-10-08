Components
==========

A GeoNode server is composed of several components running in different contexts:

GeoNode
-------
A Django application responsible for:

* Storing GeoNode-specific entities such as configured maps and user
  profiles 
* Presenting user-facing HTML pages, including OpenLayers/GeoExt 
  applications 
* Propagating data appropriately to other services (see below) 
* Hosting site-specific GeoNode extensions such as the reporting 
  applications described in this document

GeoServer
---------
A Java web application responsible for:

* Abstracting away the differences between different data storage
  formats by normalizing to the OGC standards of WFS, WMS, and WCS
* Providing server-side processing of that data
* Hosting styling and basic metadata

GeoWebCache
-----------
A Java web application (typically running as an extension to GeoServer)
responsible for:

* Caching the results of rendering operations to reduce server load

GeoNetwork
----------
A Java web application responsible for:

* Storing extended metadata for data layers hosted on the GeoNode server
* Crawling external GeoNetwork services to collect metadata for
  additional layers
* Providing search across those indexed layers
    
For the purpose of GeoNode development each of these applications will be
extended to varying degrees (for example, the GeoNode Django application is
being developed from scratch, while GeoNetwork may not even see any use this
round.) 
