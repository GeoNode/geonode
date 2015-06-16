.. _architecture:

============
Architecture
============

The Big Picture
---------------

.. figure:: img/geonode_component_architecture.png
   :align: center

   GeoNode Component Architecture
   


Django Architecture
-------------------

www.djangoproject.com

MVC/MVT
.......

MVC 
  Model, View, Controller
MVT 
  Model, View, Template

- Model represents application data and provides rich ORM functionality.
- Views are a rendering of a Model most often using the Django template engine.
- In Django, the controller part of this commonly discussed, layered architecture is a
  subject of discussion. According to the standard definition, the controller is the
  layer or component through which the user interacts and model changes occur.
    
More: http://reinout.vanrees.org/weblog/2011/12/13/django-mvc-explanation.html

WSGI
....

WSGI
  Web Server Gateway Interface (whis-gey)


- This is a python specification for supporting a common interface between all of the
  various web frameworks and an application (Apache, for example) that is 'serving'.
- This allows any WSGI compliant framework to be hosted in any WSGI compliant server.
- For most GeoNode development, the details of this specification may be ignored.
    
More: http://en.wikipedia.org/wiki/Wsgi


GeoNode and GeoServer
---------------------

GeoNode uses GeoServer for providing OGC services. 

- GeoNode configures GeoServer via the REST API
- GeoNode retrieves and caches spatial information from GeoServer. This includes
  relevant OGC service links, spatial metadata, and attribute information.
 
  In summary, GeoServer contains the layer data, and GeoNode's layer model
  extends the metadata present in GeoServer with its own.
- GeoNode can discover existing layers published in a GeoServer via the WMS
  capabilities document.
- GeoServer delegates authentication and authorization to GeoNode (see README_).
- Data uploaded to GeoNode is first processed in GeoNode and finally published
  to GeoServer (or ingested into the spatial database).

More:  http://geoserver.org

.. _README: https://github.com/GeoNode/geoserver-geonode-ext/blob/master/README.md

GeoNode and PostgreSQL/PostGIS
------------------------------

In production, GeoNode is configured to use PostgreSQL/PostGIS for it's persistent
store. In development and testing mode, often an embedded sqlite database is used.
The latter is not suggested for production.

- The database stores configuration and application information. This includes
  users, layers, maps, etc.
- It is recommended that GeoNode be configured to use PostgresSQL/PostGIS for 
  storing vector data as well. While serving layers directly from shapefile
  allows for adequate performance in many cases, storing features in the database
  allows for better performance especially when using complex style rules based
  on attributes.


GeoNode and pycsw
-----------------

GeoNode is built with `pycsw <http://pycsw.org>`_ embedded as the default CSW server component.

Publishing
..........

Since pycsw is embedded in GeoNode, layers published within GeoNode are automatically published
to pycsw and discoverable via CSW.  No additional configuration or actions are required to publish
layers, maps or documents to pycsw.

Discovery
.........

GeoNode's CSW endpoint is deployed available at ``http://localhost:8000/catalogue/csw`` and is
available for clients to use for standards-based discovery.  See http://docs.pycsw.org/en/latest/tools.html
for a list of CSW clients and tools.

Javascript in GeoNode
---------------------

- GeoExplorer runs in the browser and talks with GeoNode and GeoServer's APIs
  using AJAX.
- jQuery is used for incremental enhancement of many GeoNode HTML interfaces.
