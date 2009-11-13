Proxy Service
=============

In order to better support JavaScript applications, the GeoNode will
incorporate a proxy service to help GeoExt and OpenLayers applications access
data from remote services (the proxy service is necessary due to the
`Same-Origin Policy <http://en.wikipedia.org/wiki/Same_origin_policy>`_).

Endpoint
--------

The proxy service will be implemented as a single endpoint:

:file:`/proxy` 
    Accepts a URL as a URL-encoded query parameter and forwards the request to
    that URL.  Any headers, cookies, or other details that might allow session
    hijacking or other security risks must be stripped.

Deployment Concerns
-------------------

While there should be an integrated proxy service for development purposes, it
will likely be more secure and reliable to use an external proxy for production
environments.

.. todo:: 

    How do we handle this and other differences between development and 
    production installations of the GeoNode?
