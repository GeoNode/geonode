Logging In GeoNode
==================

This page describes how to get more information if something goes wrong in a
GeoNode site.  There are two main logs for GeoNode deployments:

Servlet Container Logs
----------------------

GeoNetwork and GeoServer both use standard servlet container logging. For
example, if you are using Tomcat in its default configuration, the logs from
GeoServer and GeoNetwork will be intermingled in
``[Tomcat installation directory]/logs/catalina.out`` . GeoNetwork also
produces separated logs in
``[Tomcat installation directory]/logs/geonetwork.log``, and GeoServer produces
separated logs in ``[GeoServer data directory]/logs/geoserver.log``.  Note that
while GeoNetwork and Tomcat log inside the Tomcat installation directory,
GeoServer keeps logs inside the GeoServer configuration directory.

Django Logging
--------------

GeoNode uses the standard Python ``logging`` module to log certain events.  By
default these log messages are not recorded anywhere, so you must configure a
log destination in your Django ``local_settings.py``.  If you are running the
Django application in Apache with mod_wsgi and would like to keep the log
messages in Apache's error log, you can add a section like this to
``local_settings.py``::

    import logging
    for _module in ["geonode.maps.views", "geonode.maps.gs_helpers"]:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        # The earlier a level appears in this list, the more output it will produce in the log file.
        _logger.setLevel(logging.WARNING)

If you would like to log to a specific file instead, you can use this snippet
instead::

    import logging
    for _module in ["geonode.maps.views", "geonode.maps.gs_helpers"]:
        _logger = logging.getLogger(_module)

        # stream handler logs to standard error stream,
        # or apache error log when running under mod_wsgi
        _logger.addHandler(logging.StreamHandler()) 

        # alternatively, you can log to specific file like so:
        # _logger.addHandler(logging.FileHandler("/path/to/logs/geonode-django.log"))

        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        # The earlier a level appears in this list, the more output it will produce in the log file.
        _logger.setLevel(logging.WARNING)
