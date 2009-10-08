Map Django App
==============

The Map App manages the maps created through the GeoExt map editor.

Model
-----

The Map App represents maps as several entities in the database:

1. ``Map``: Houses map metadata, as well as references to the other objects
   incorporated into the map.  Each ``Map`` contains the following fields:

   ``title``
       The title of the map, also used as a short name in listings

   ``abstract``
       Provides a more detailed description of the map's contents.

   ``contact``
       Information on who created the map.  Eventually this might be tied to a
       Django user account, but it is a simple string for the current 
       iteration.

   ``featured``
       A boolean flag indicating whether this map should show up on an
       endorsed list (ie, the CAPRA Maps section in the CAPRA GeoNode) or on a
       segregated, less strictly reviewed list (ie, the Community section).

       .. todo:: 

           Does the ``featured`` field belong on Map records, or should
           it be an extension to the base map editing functionality?

   ``zoom``
       A number indicating the zoom level at which to start the map (using 0
       to indicate world bounds.)  

       .. todo:: Is there a maximum allowable zoom level?

   ``center_lat``
       The latitude that the map should center on at startup

   ``center_lon``
       The longitude that the map should center on at startup

2. ``Layer``: References a particular data layer used in the map.  Each
   ``Layer`` contains the following fields:

   ``name``
       The display name for the layer.

   ``ows_url``
       The OWS service endpoint to use for fetching tiles and data from this
       layer.

   ``group``
       A grouping that affects layer display.  The grouping values that are
       respected include:
       
       ``background``: the background group displays below all other groups.
           Additionally, only on layer in the background group may be visible 
           at a time.

       Any layers whose grouping values are not known will simply be displayed
       "normally;" that is, they will be rendered immediately above the
       background group and may have multiple layers visible simultaneously.

       .. todo:: 

           Since the ``group`` field only has one respected value,
           should we collapse it to a boolean flag instead of a string?

   ``stack_order``
       An integer value that is not displayed directly, but used to control
       the layer ordering in the map.  Lower stack order values cause layers
       to show up below others in the map display.

   ``map``
       The ``Map`` record to which the layer "belongs".  Each layer is 
       associated with a single map.

       .. note:: 
       
           Since layers are map-specific, they are not suitable for
           storing general-purpose metadata such as tags or abstracts.

   .. todo:: Do we need to support any layer types aside from OWS?

Extending
---------
 
Beyond matching the existing functionality, we will need to consider:

* Adding support for specifying the style of a layer in a map
* Adding support for specifying the opacity of a layer in a map
* Tracking metadata for layers

REST API
--------
In order to make the maps more accessible to JavaScript applications,  the
maps will be exposed via a REST service.  The API will be the following:

    GET :file:`/maps/`
        A listing of all maps known to the server, including map metadata so
        that a human-readable listing can be displayed to the user.
        
        A sample JSON response::

            [{
                "id1": {
                    "title": "A Map",
                    "abstract": "This is a map",
                    "contact": "The Mapmaker"
                }
            }]

    POST :file:`/maps/`
        Add a map to the list.  The map representation should match that
        described below.  On success, a map id will be returned in an HTTP
        ``Location`` header on a response with a ``201 Created`` status.

    GET :file:`/maps/{id}`
        Get the full representation of a single map (for opening in the map
        viewer, etc.)  This representation will be directly usable as a
        configuration for the map viewing application.

        .. seealso:: 

             :doc:`/geonode-core/map-viewer` for information about this 
             configuration object.

.. todo:: 

    Investigate the 
    `Piston <http://bitbucket.org/jespern/django-piston/wiki/Home>`_
    Django extension for simplifying the implementation of this API

Administration
--------------

For the current iteration, map administration will be provided using the
excellent administration interface provided by Django.
