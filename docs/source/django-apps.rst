GeoNode Django Apps
===================

The user interface of a GeoNode site is built on top of the Django web
framework.  GeoNode includes a few "apps" (reusable Django modules) to support
development of those user interfaces.  While these apps have reasonable default
configurations, for customized GeoNode sites you will probably want to adjust
these apps for your specific needs.

.. toctree::
   :maxdepth: 2

   django-apps/core
   django-apps/maps
   django-apps/proxy

.. comment:

    geonode.core
      Provide site navigation support and other miscellaneous tasks

    geonode.maps
      manage layers, maps, styles

    geonode.proxy
      support JavaScript applications accessing GeoServer/GeoNetwork
