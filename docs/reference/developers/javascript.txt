.. _javascript:

=====================
JavaScript in GeoNode
=====================

GeoNode provides a number of facilities for interactivity in the web browser built on top of several high-quality JavaScript frameworks:

* `Bootstrap <http://getbootstrap.com/>`_ for GeoNode's front-end user interface and common user interaction.
* `Bower <http://bower.io/>`_ for GeoNode's front-end package management.
* `ExtJS <http://extjs.com/>`_ for component-based UI construction and data access
* `OpenLayers <http://openlayers.org/>`_ for interactive mapping and other geospatial operations
* `GeoExt <http://geoext.org/>`_ for integrating ExtJS with OpenLayers
* `Grunt <http://gruntjs.com/>`_ for front-end task automation.
* `GXP <http://projects.opengeo.org/gxp>`_ for providing some higher-level application building facilities on top of GeoExt, as well
  as improving integration with GeoServer.
* `jQuery <http://jquery.com>`_ to abstract javascript manipulation, event handling, animation and Ajax.

GeoNode uses application-specific modules to handle pages and services that are unique to GeoNode.  This framework includes:

* A `GeoNode mixin <https://github.com/GeoNode/geonode/blob/master/geonode/static/geonode/js/extjs/GeoNode-mixin.js>`_  class
  that provides GeoExplorer with the methods needed to properly function in GeoNode.  The class
  is responsible for checking permissions, retrieving and submitting the `CSRF token <https://docs.djangoproject.com/en/dev/ref/contrib/csrf/>`_,
  and user authentication.

* A `search module <https://github.com/GeoNode/geonode/tree/master/geonode/static/geonode/js/search>`_ responsible for the GeoNode's site-wide search functionality.
* An `upload and status module <https://github.com/GeoNode/geonode/tree/master/geonode/static/geonode/js/upload>`_ to support file uploads.
* `Template files <https://github.com/GeoNode/geonode/tree/master/geonode/static/geonode/js/templates>`_ for generating commonly used html sections.
* A `front-end testing module <https://github.com/GeoNode/geonode/tree/master/geonode/static/geonode/js/tests>`_ to test GeoNode javascript.

The following concepts are particularly important for developing on top of the
GeoNode's JavaScript framework.

* Components - Ext components handle most interactive functionality in
  "regular" web pages.  For example, the scrollable/sortable/filterable table
  on the default Search page is a Grid component.  While GeoNode does use some
  custom components, familiarity with the idea of Components used by ExtJS is
  applicable in GeoNode development.

* Viewers - Viewers display interactive maps in web pages, optionally decorated
  with Ext controls for toolbars, layer selection, etc.  Viewers in GeoNode use
  the GeoExplorer base class, which builds on top of GXP's Viewer to provide
  some common functionality such as respecting site-wide settings for
  background layers. Viewers can be used as components embedded in pages, or
  they can be full-page JavaScript applications.

* Controls - Controls are tools for use in OpenLayers maps (such as a freehand
  control for drawing new geometries onto a map, or an identify control for
  getting information about individual features on a map.)  GeoExt provides
  tools for using these controls as ExtJS "Actions" - operations that can be
  invoked as buttons or menu options or associated with other events.
