# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from geonode.qgis_server.views import download_zip, tile

__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'urls'
__date__ = '1/29/16'
__copyright__ = 'imajimatika@gmail.com'

urlpatterns = patterns(
    '',
    url(
        r'^qgis-server/download-zip/(?P<layername>[^/]*)$',
        download_zip,
        name='qgis-server-download-zip'
    ),
)
