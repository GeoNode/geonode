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

NAVBAR
  The configuration for the site navbar.  This is either a 2-level dict, or the
  path to a ConfigParser configuration file.  In either case, the configuration
  provides named links with some extra metadata, in the following format::

    { "data": {
        "id": "%sLink", # the HTML id for the <a> element of this link, will be
          # interpolated with the link name
        "item_class", # the HTML class for the <li> element wrapping the link
        "link_class", # the HTML class for the link itself
        "text", # the text for the link
        "url", # the view to link to
        }
    }

  The special entry 'meta' provides some additional configuration::
    
    { "meta": {
        "active_class": "here", # the class to use for the link to the current 
          # page
        "default_id": "%sLink", # the default id, will be interpolated with the
          # link name
        "default_item_class": "", # the default class for the <li> wrapping
        "default_link_class"
          # each link
        "default_link_class": "", # the default class for the <a> element for
          # each link
        "end_class": "last", # the class for the last link in the list
        "visible": "data index maps", # space-separated list of the links that
          # should actually be included in pages; this allows controlling the
          # ordering, and also provides for a 'dummy' link that isn't included
          # in the navbar, so you can use that on pages that aren't top-level
          # enough to appear in the navbar.
        }
    }


Template Tags
-------------

geonode_media <media_name>
  Accesses entries in MEDIA_LOCATIONS without requiring the view to explicitly
  add it to the template context.  Example usage::

  {% include geonode_media %}
  {% geonode_media "ext_base" %}
  
navbar <page> [template]
  Include the GeoNode navigation bar in a page.  The ``page`` argument
  identifies the page from the configuration that should be considered current.
  The optional ``template`` argument selects a template to use for rendering
  the navigation bar.  You can see an example template in the source for the
  module.  Example usage::

  {% include navbar %}
  {% navbar home %}
