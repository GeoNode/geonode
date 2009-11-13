Data Upload
===========

For upload, we need to do the following:

* Collect a dataset (eg, a zip archive containing a Shapefile and friends)
* Verify that GeoServer can read it (and report what's wrong to the user if not)
* Auto-populate any metadata fields that we can from the data
* Present a form to the user so he can manually complete the metadata

The form itself will be presented by Django, but the data validation ultimately falls to GeoServer.  So, we need to wrap those error messages somehow.  Options for doing so that have been discussed so far:

* Have the form submit directly to GeoServer; use JavaScript to interpret the
  result and format error message for the user.
* Have the form submit back to Django, which then forwards the request to
  GeoServer and proxies error messages, potentially formatting them along the
  way.

Benefits of going through Django:

* No funky browser tricks to submit a form without reloading the page
* Can hang on to the uploaded file if GeoServer is down for some reason
* Potentially better progress reporting

Benefits of going straight to GeoServer:

* Simpler
* Lets us rely on GeoServer's authentication system to prevent unauthorized
  uploads.
* Avoid implementing a GeoServer RESTConfig client in Django

.. todo:: 

    Elaborate on these upload options to try and reach a conclusion.

.. todo:: 

    Determine if the upload process integrates at all with GeoNode extensions
    such as the :doc:`../reporting-application/category-application`.

When :doc:`../geonode-core/data-styling` is supported, it may be integrated into the upload
process as an additional, final step.
