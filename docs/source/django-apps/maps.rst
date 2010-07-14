``geonode.maps`` - Map creation and geospatial data management
==============================================================

This Django app provides some support for managing and manipulating geospatial
datasets.  In particular, it provides tools for editing, viewing, and searching
metadata for data layers, and for editing, viewing, and searching maps that
aggregate data layers to display data about a particular topic.

Models
------

The maps app provides two main model types:

* Layer - A data layer managed by the GeoNode

* Map - A collection of data layers composed in a particular order to form a map

Additionally, there is a MapLayer model that maintains some map-specific
information related to a layer, such as the z-indexing order.

Views
-----

The maps app provides views for:

* Creating, viewing, browsing, editing, and deleting Maps
* Creating, viewing, browsing, editing, and deleting Layers and their metadata

These operations require the use of GeoServer and GeoNetwork to manage map
rendering and metadata indexing, as well as GeoExt to provide interactive
editing and previewing of maps and data layers.

There are also some url mappings in the geonode.maps.urls module for easy
inclusion in GeoNode sites.

``settings.py`` Entries
-----------------------

GEOSERVER_CREDENTIALS 
  A 2-tuple with the username and password for a user with privileges to manage
  data in the GeoServer coupled to this GeoNode.

GEOSERVER_BASE_URL
  A base URL from which GeoNode can construct GeoServer service URLs.  This is
  the servlet context URL for the servlet container, or you can determine it by
  visiting the GeoServer administration app's home page without the /web/ at
  the end.  If your GeoServer administration app is at
  http://example.com/geoserver/web/ , your GEOSERVER_BASE_URL is
  http://example.com/ .

GEONETWORK_CREDENTIALS
  Similar to GEOSERVER_CREDENTIALS, but for GeoNetwork.  The user must have
  permissions to create and modify metadata records in GeoNetwork.

GEONETWORK_BASE_URL
  Similar to GEOSERVER_BASE_URL, but for GeoNetwork.  Again, this is the
  servlet context URL, or can be determined by stripping the last path
  component off the url for the GeoNetwork homepage.

SITEURL
  A base URL for use in creating absolute links to Django views.

DEFAULT_MAP_BASE_LAYER
  The name of the background layer to include in newly created maps.
 
DEFAULT_MAP_CENTER
  A 2-tuple with the latitude/longitude coordinates of the center-point to use
  in newly created maps.
 
DEFAULT_MAP_ZOOM
  The zoom-level to use in newly created maps.  This works like the OpenLayers
  zom level setting; 0 is at the world extent and each additional level cuts
  the viewport in half in each direction.
  
GOOGLE_API_KEY
  A Google Maps v2 API key to use when a Google Maps background layer is used.


``django-admin.py`` Commands
----------------------------

updatelayers
  Scan GeoServer for data that hasn't been added to the GeoNode yet, and ensure
  that each layer in the Django database is indexed in GeoNetwork
