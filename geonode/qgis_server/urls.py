# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from geonode.qgis_server.views import (
    download_zip,
    tile,
    legend,
    thumbnail,
    map_thumbnail,
    qgis_server_request,
    qgis_server_pdf,
    qgis_server_map_print
)
from views import geotiff

__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'urls'
__date__ = '1/29/16'
__copyright__ = 'imajimatika@gmail.com'

urlpatterns = patterns(
    '',
    url(
        r'^qgis-server/download-zip/(?P<layername>[^/]*)'
        r'[\?]?'
        r'(?:&access_token=(?P<access_token>[\w]*))?$',
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
        r'^qgis-server/geotiff/'
        r'(?P<layername>[\w]*)'
        r'[\?]?'
        r'(?:&access_token=(?P<access_token>[\w]*))?$',
        geotiff,
        name='qgis-server-geotiff'
    ),
    url(
        r'^qgis-server/legend/(?P<layername>[\w]*)'
        r'(?:/(?P<layertitle>[\w]*))?'
        r'[\?]?'
        r'(?:&access_token=(?P<access_token>[\w]*))?$',
        legend,
        name='qgis-server-legend'
    ),
    # url(
    #     r'^qgis-server/legend/(?P<layername>[^/]*)$',
    #     legend,
    #     name='qgis-server-legend'
    # ),
    url(
        r'^qgis-server/thumbnail/(?P<layername>[\w]*)$',
        thumbnail,
        name='qgis-server-thumbnail'
    ),
    url(
        r'^qgis-server/map/thumbnail/(?P<map_id>[\w]*)$',
        map_thumbnail,
        name='qgis-server-map-thumbnail'
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
