# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.conf.urls import patterns, url

from geonode.qgis_server.views import (
    download_zip,
    tile,
    legend,
    thumbnail,
    map_thumbnail,
    qgis_server_request,
    qgis_server_pdf,
    qgis_server_map_print,
    geotiff
)


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
    # WMS entry point, this URL is not specific to WMS, you should remove it ?
    url(
        r'^qgis-server/wms/$',
        qgis_server_request,
        name='qgis-server-request'
    ),
    # Generic OGC entry points
    url(
        r'^qgis-server/ogc/$',
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
