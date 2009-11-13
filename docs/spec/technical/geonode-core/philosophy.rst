What is GeoNode Core?
=====================

The GeoNode Core defines the basic functionality that GeoNode installations
provide, and some facilities for individual installations to implement extra,
specialized functionality for their own needs.  This core functionality
includes:

* A :doc:`../geonode-core/map-application` for managing maps and map layers,
  using GeoServer to provide robust, OGC-standard-compliant services for
  accessing them.
* Facilities for synchronizing metadata on map layers with external services
  such as GeoNetwork.  
* A basic site providing search, browsing and editing functions for maps, data
  layers, and styles, including :doc:`../geonode-core/data-upload`,
  :doc:`../geonode-core/data-styling` and a :doc:`map-viewer`.
* Reusable Django components for replacing or augmenting that site to suit
  specific needs.

Very particular applications such as :doc:`reporting applications
<../reporting-application/index>` are supported, but not included in the core
GeoNode functionality.

