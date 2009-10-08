Static Templates
================

In order to pave the way for the GeoNode to take advantage of Django for
server-side processing, the existing static pages will need to be converted to
Django templates.  This is relatively straightforward; since they are currently
static documents there is no need to worry about setting up models or
interpolating values into the documents. 

.. note:: 
    The Map editor is a notable exception; see :doc:`/geonode-core/map-viewer`
    for details.

The pages include:

* Help: Describes the purpose and basic usage of the GeoNode
* Developer: Describes how developers (and GIS experts) can use the OGC standard
  services exposed by the GeoNode
* Data: Provides a listing of layers housed in the GeoNode
* Home: Displays a "featured" map and introduces the GeoNode to newcomers.
* Featured Maps: Provides a listing of CAPRA-endorsed maps on the GeoNode
* Community Maps: Provides a listing of contributed maps that have not been
  reviewed and endorsed by CAPRA staff
* :doc:`/geonode-core/map-viewer`: Allows editing of maps on the GeoNode.

The template conversion process should have minimal change on the functionality
of the application (although some changes to the map viewer will happen.)  We
should take this opportunity to create a base template that all pages can
"inherit" from, avoiding duplication of things like the navigation toolbar and
CSS includes.

Navigation Handling
-------------------

One particular advantage of using templates is the ability to "factor out" the navigation bar which has been disproportionately annoying to maintain in the static HTML version of the GeoNode.  

URL Structure
-------------

Switching to Django also makes it straightforward to "clean up" our URLs a bit,
eliminating file extensions etc.  For the pages described above, the URL structure should be:

:file:`/`
   the Home page 

:file:`/about`
   the Help page

:file:`/data`
   the Data page

:file:`/developer`
   the Developer page

:file:`/maps`
   the Featured Maps page

:file:`/community`
   the Community Maps page

.. note:: 

    The Map Viewer intentionally is not given its own tab in the navigation 
    tabs.
   
This rearrangement of the URL structure means that special care should be given
to ensuring that internal links continue to function properly, especially
including the map storage service which will need to be ported from the
existing GeoServer extension.

.. seealso:: 
    http://bitbucket.org/sbenthall/djupacapra/ is an experiment in porting the
    GeoNode to Django.  The templates there should be of some use.
