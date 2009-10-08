Data Styling
============

In order to support data styling, we need to start by refactoring the existing
Styler application into reusable GeoExt components.  Some notes on the
refactoring are available at http://projects.opengeo.org/styler .

In addition to the basic vector styling supported by these components, we will
need to provide for raster styling, including:

* Setting transparency for no-data cells in the coverage
* Creating simple color ramps
* Getting some statistics for a coverage layer (range of values, standard
  deviation, etc.)

.. seealso:: 
   
   http://projects.opengeo.org/geoext/wiki/RasterSymbolizers provides some
   thoughts regarding the UI requirements of styling raster graphics.

Style editing also presents some complications in combination with caching.  

.. todo::

    Determine whether GeoWebCache is able to truncate its caches when layer
    styles change.
