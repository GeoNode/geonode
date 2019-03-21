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

from django.conf.urls import url

from geonode.qgis_server.views import (
    download_zip,
    download_qgs,
    download_map,
    tile,
    tile_404,
    legend,
    layer_ogc_request,
    qgis_server_request,
    qgis_server_pdf,
    qgis_server_map_print,
    geotiff,
    download_qlr,
    qml_style, set_thumbnail, default_qml_style)


urlpatterns = [
    # Specific for a QGIS Layer
    # '',
    url(
        r'^download-zip/(?P<layername>[\w]*)$',
        download_zip,
        name='download-zip'
    ),
    url(
        r'^download-qgs/(?P<layername>[\w]*)$',
        download_qgs,
        name='download-qgs'
    ),
    url(
        r'^download-map/(?P<mapid>\d+)$',
        download_map,
        name='download-map'
    ),
    url(
        r'^tiles/'
        r'(?P<layername>[^/]*)/'
        r'(?P<z>[0-9]*)/'
        r'(?P<x>[0-9]*)/'
        r'(?P<y>[0-9]*).png$',
        tile,
        name='tile'
    ),
    url(
        r'^tiles/'
        r'(?P<layername>[^/]*)/'
        r'(?P<style>[^/]*)/'
        r'(?P<z>[0-9]*)/'
        r'(?P<x>[0-9]*)/'
        r'(?P<y>[0-9]*).png$',
        tile,
        name='tile'
    ),
    url(
        r'^tiles/'
        r'(?P<layername>[^/]*)/'
        r'(?P<style>[^/]*)/'
        r'\{z\}/\{x\}/\{y\}.png$',
        tile_404,
        name='tile'
    ),
    url(
        r'^tiles/'
        r'(?P<layername>[^/]*)/\{z\}/\{x\}/\{y\}.png$',
        tile_404,
        name='tile'
    ),
    url(
        r'^geotiff/(?P<layername>[\w]*)$',
        geotiff,
        name='geotiff'
    ),
    url(
        r'^legend/(?P<layername>[\w]*)/'
        r'(?P<style>[\w]*)/'
        r'(?:/(?P<layertitle>(True|False)))?$',
        legend,
        name='legend'
    ),
    url(
        r'^legend/(?P<layername>[\w]*)(?:/(?P<layertitle>(True|False)))?$',
        legend,
        name='legend'
    ),
    url(
        r'^ogc/(?P<layername>[\w]+)$',
        layer_ogc_request,
        name='layer-request'
    ),

    # Generic for OGC
    # WMS entry point, this URL is not specific to WMS, you should remove it ?
    url(
        r'^wms/$',
        qgis_server_request,
        name='request'
    ),
    url(
        r'^ogc/$',
        qgis_server_request,
        name='request'
    ),

    # Generic for the app
    url(
        r'^pdf/info\.json$',
        qgis_server_pdf,
        name='pdf'
    ),
    url(
        r'^map/print$',
        qgis_server_map_print,
        name='map-print'
    ),
    url(
        r'^style/default/(?P<layername>[^/]*)(?:/(?P<style_name>[^/]*))?$',
        default_qml_style,
        name='default-qml'
    ),
    url(
        r'^style/upload/(?P<layername>[^/]*)(?:/(?P<style_name>[^/]*))?$',
        qml_style,
        name='upload-qml'
    ),
    url(
        r'^style/remove/(?P<layername>[^/]*)/(?P<style_name>[^/]*)$',
        qml_style,
        name='remove-qml'
    ),
    url(
        r'^style/download/(?P<layername>[^/]*)(?:/(?P<style_name>[^/]*))?$',
        qml_style,
        name='download-qml'
    ),
    url(
        r'^thumbnail/set/(?P<layername>[^/]*)$',
        set_thumbnail,
        name='set-thumbnail'
    ),
    url(
        r'^download-qlr/(?P<layername>[\w]*)$',
        download_qlr,
        name='download-qlr'
    ),
]
