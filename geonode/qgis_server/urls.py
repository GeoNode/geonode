# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from geonode.qgis_server.views import (
    download_zip,
    tile,
    legend,
    thumbnail,
    qgis_server_request,
    qgis_server_pdf,
    qgis_server_map_print
)

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
    url(
        r'^qgis-server/'
        r'tiles/'
        r'(?P<layername>[^/]*)/'
        r'(?P<z>[0-9]*)/'
        r'(?P<x>[0-9]*)/'
        r'(?P<y>[0-9]*).png$',
        tile,
        name='qgis-server-tile'
    ),
    url(
        r'^qgis-server/legend/(?P<layername>[^/]*)'
        r'(?:/(?P<layertitle>[^/]*))?$',
        legend,
        name='qgis-server-legend'
    ),
    # url(
    #     r'^qgis-server/legend/(?P<layername>[^/]*)$',
    #     legend,
    #     name='qgis-server-legend'
    # ),
    url(
        r'^qgis-server/thumbnail/(?P<layername>[^/]*)$',
        thumbnail,
        name='qgis-server-thumbnail'
    ),
    url(
        r'^qgis-server/wms/$',
        qgis_server_request,
        name='qgis-server-request'
    ),
    url(
        r'^qgis-server/pdf/info\.json$',
        qgis_server_pdf,
        name='qgis-server-pdf'
    ),
    url(
        r'^qgis-server/map/print$',
        qgis_server_map_print,
        name='qgis-server-map-print'
    ),
)
