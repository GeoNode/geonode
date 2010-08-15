``geonode.proxy`` - Assist JavaScript applications in accessing remote servers
==============================================================================

This Django app provides some HTTP proxies for accessing data from remote
servers, to overcome restrictions imposed by the same-origin policy used by
browsers.  This helps the GeoExt applications in a GeoNode site to access various XML documents from OGC-compliant data services.

Views
-----

geonode.proxy.views.proxy
  This view forwards requests without authentication to a URL provided in the
  request, similar to the proxy.cgi script provided by the OpenLayers project.

geonode.proxy.views.geoserver
  This view proxies requests to GeoServer.  Instead of a URL-encoded URL
  parameter, the path component of the request is expected to be a path
  component for GeoServer.  Requests to this URL require valid authentication
  against the Django site, and will use the GEOSERVER_CREDENTIALS and
  GEOSERVER_BASE_URL settings as defined in the maps application.
