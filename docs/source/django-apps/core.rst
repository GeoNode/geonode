``geonode.core`` - Miscellaneous site utilities
===============================================

This Django app provides some basic website features in an extensible fashion.
For example, many sites should be able to add tabs to the site navigation bar
without having to modify templates by taking advantage of the navigation
features provided by this module.

``settings.py`` Entries
-----------------------

MEDIA_LOCATIONS
  GeoNode uses a lot of JavaScript and CSS includes due to the distribution
  restrictions imposed by ExtJS.  The MEDIA_LOCATIONS settings file should be a
  Python dict providing mappings from abstracted library prefixes to actual
  media URLs, suitable for use in the site.  To see the prefix names used in
  the default templates, an example, consult the settings.py for the example
  ``geonode`` site included in the source tree.

Template Tags
-------------

geonode_media <media_name>
  Accesses entries in MEDIA_LOCATIONS without requiring the view to explicitly
  add it to the template context.  Example usage::

  {% include geonode_media %}
  {% geonode_media "ext_base" %}
