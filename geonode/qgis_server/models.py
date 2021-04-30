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

import logging
import os
from shutil import rmtree
from xml.etree import ElementTree

import requests
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from geonode.security.models import PermissionLevelMixin
from lxml import etree
from defusedxml import lxml as dlxml
from six import string_types

from geonode import qgis_server
from geonode.compat import ensure_string
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.utils import check_ogc_backend

logger = logging.getLogger("geonode.qgis_server.models")

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    QGIS_LAYER_DIRECTORY = settings.QGIS_SERVER_CONFIG['layer_directory']
    QGIS_TILES_DIRECTORY = settings.QGIS_SERVER_CONFIG['tiles_directory']

    if not os.path.exists(QGIS_LAYER_DIRECTORY):
        os.mkdir(QGIS_LAYER_DIRECTORY)


class QGISServerLayer(models.Model, PermissionLevelMixin):
    """Model for Layer in QGIS Server Backend.
    """

    accepted_format = [
        'tif', 'tiff', 'asc', 'shp', 'shx', 'dbf', 'prj', 'qml', 'xml', 'qgs']

    geotiff_format = ['tif', 'tiff']

    ascii_format = ['asc']

    layer = models.OneToOneField(
        Layer,
        primary_key=True,
        related_name='qgis_layer',
        on_delete=models.CASCADE
    )
    base_layer_path = models.CharField(
        name='base_layer_path',
        verbose_name='Base Layer Path',
        help_text='Location of the base layer.',
        max_length=2000
    )

    default_style = models.ForeignKey(
        'qgis_server.QGISServerStyle',
        related_name='layer_default_style',
        default=None,
        null=True,
        on_delete=models.SET_NULL)
    styles = models.ManyToManyField(
        'qgis_server.QGISServerStyle',
        related_name='layer_styles')

    @property
    def files(self):
        """Returned all files related with this layer.

        :return: List of related paths
        :rtype: list(str)
        """
        base_path = self.base_layer_path
        base_name, __ = os.path.splitext(base_path)
        extensions_list = list(QGISServerLayer.accepted_format)

        # QGIS can create a .aux.xml too
        extensions_list += ['.aux.xml']
        found_files = []
        for ext in extensions_list:
            file_path = f'{base_name}.{ext}'
            if os.path.exists(file_path):
                found_files.append(file_path)
        return found_files

    @property
    def qgis_layer_path_prefix(self):
        """Returned QGIS layer path prefix.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        Path prefix: /usr/src/app/geonode/qgis_layer/jakarta_flood
        """
        prefix, __ = os.path.splitext(self.base_layer_path)
        return prefix

    @property
    def qgis_layer_name(self):
        """Returned QGIS Layer name associated with this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS Layer name: jakarta_flood
        """
        return os.path.basename(self.qgis_layer_path_prefix)

    @property
    def qgis_project_path(self):
        """Returned QGIS Project path related with this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS Project path: /usr/src/app/geonode/qgis_layer/jakarta_flood.qgs
        """
        return f'{self.qgis_layer_path_prefix}.qgs'

    @property
    def cache_path(self):
        """Returned the location of tile cache for this layer.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS cache path: /usr/src/app/geonode/qgis_tiles/jakarta_flood

        :return: Base path of layer cache
        :rtype: str
        """
        return os.path.join(QGIS_TILES_DIRECTORY, self.qgis_layer_name)

    @property
    def qml_path(self):
        """Returned the location of QML path for this layer (if any).

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS QML path: /usr/src/app/geonode/qgis_tiles/jakarta_flood.qml

        :return: Base path of qml style
        :rtype: str
        """
        return f'{self.qgis_layer_path_prefix}.qml'

    def delete_qgis_layer(self):
        """Delete all files related to this object from disk."""
        for file_path in self.files:
            try:
                os.remove(file_path)
            except OSError:
                pass

        # Removing the cache.
        path = self.cache_path
        logger.debug(f'Removing the cache from a qgis layer : {path}')
        try:
            rmtree(path)
        except OSError:
            pass

        # Removing orphaned styles
        for style in QGISServerStyle.objects.filter(layer_styles=None):
            style.delete()

    def get_self_resource(self):
        """Get associated resource base."""
        # Associate this model with resource
        try:
            return self.layer.get_self_resource()
        except Exception:
            return None

    class Meta:
        app_label = "qgis_server"


class QGISServerStyle(models.Model, PermissionLevelMixin):
    """Model wrapper for QGIS Server styles."""
    name = models.CharField(_('style name'), max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)
    body = models.TextField(_('style xml'), null=True, blank=True)
    style_url = models.CharField(_('style url'), null=True, max_length=1000)
    style_legend_url = models.CharField(
        _('style legend url'), null=True, max_length=1000)

    @classmethod
    def from_get_capabilities_style_xml(
            cls, qgis_layer, style_xml, style_url=None, synchronize=True):
        """Convert to this model from GetCapabilities Style tag.

        :param qgis_layer: Associated QGIS Server Layer
        :type qgis_layer: QGISServerLayer

        :param style_xml: xml string or object
        :type style_xml: str | lxml.etree.Element |
            xml.etree.ElementTree.Element

        :param style_url: style information stored as xml
        :type style_url: str

        :param synchronize: Flag, if true then synchronize the new value
        :type synchronize: bool

        :return: QGISServerStyle model and boolean flag created
        :rtype: QGISServerStyle, bool
        """

        if isinstance(style_xml, string_types):
            style_xml = dlxml.fromstring(style_xml)

        elif isinstance(style_xml, ElementTree.Element):
            style_xml = dlxml.fromstring(
                ElementTree.tostring(
                    style_xml, encoding='utf-8', method='xml'))

        namespaces = {
            'wms': 'http://www.opengis.net/wms',
            'xlink': 'http://www.w3.org/1999/xlink'
        }

        filter_dict = {
            'name': style_xml.xpath(
                'wms:Name', namespaces=namespaces)[0].text,

            'layer_styles': qgis_layer
        }

        # if style_body is none, try fetch it from QGIS Server
        if not style_url:
            from geonode.qgis_server.helpers import style_get_url
            style_url = style_get_url(
                qgis_layer.layer, filter_dict['name'], internal=False)

        response = requests.get(style_url)
        style_body = etree.tostring(
            dlxml.fromstring(ensure_string(response.content)), pretty_print=True)

        default_dict = {
            'title': style_xml.xpath(
                'wms:Title', namespaces=namespaces)[0].text,

            'style_legend_url': style_xml.xpath(
                'wms:LegendURL/wms:OnlineResource',
                namespaces=namespaces)[0].attrib[
                '{http://www.w3.org/1999/xlink}href'],

            'style_url': style_url,

            'body': style_body
        }

        # filter_dict['defaults'] = default_dict

        # Can't use get_or_create function for some reason.
        # So use regular query

        try:
            style_obj = QGISServerStyle.objects.get(**filter_dict)
            created = False
        except QGISServerStyle.DoesNotExist:
            style_obj = QGISServerStyle(**default_dict)
            style_obj.name = filter_dict['name']
            style_obj.save()
            created = True

        if created or synchronize:
            # Try to synchronize this model with the given parameters
            style_obj.name = filter_dict['name']

            style_obj.style_url = default_dict['style_url']
            style_obj.body = default_dict['body']
            style_obj.title = default_dict['title']
            style_obj.style_legend_url = default_dict['style_legend_url']
            style_obj.save()

            style_obj.layer_styles.add(qgis_layer)
            style_obj.save()

        return style_obj, created

    @property
    def style_tile_cache_path(self):
        """Returned the location of tile cache for this layer style.

        Example base path: /usr/src/app/geonode/qgis_layer/jakarta_flood.shp

        QGIS cache path: /usr/src/app/geonode/qgis_tiles/jakarta_flood/
            default_style

        :return: Base path of layer cache
        :rtype: str
        """
        return os.path.join(
            QGIS_TILES_DIRECTORY, self.layer_styles.first().layer.name, self.name)

    def get_self_resource(self):
        """Get associated resource base."""
        # Associate this model with resource
        try:
            qgis_layer = self.layer_styles.first()
            """:type: QGISServerLayer"""
            return qgis_layer.get_self_resource()
        except Exception:
            return None

    class Meta:
        app_label = "qgis_server"


class QGISServerMap(models.Model, PermissionLevelMixin):
    """Model wrapper for QGIS Server Map."""

    map = models.OneToOneField(
        Map,
        primary_key=True,
        name='map',
        on_delete=models.CASCADE
    )

    map_name_format = 'map_{id}'

    @property
    def qgis_map_name(self):
        """Returned QGIS Map name associated with this layer.

        based on map_name_format
        Example QGIS Map name: map_1
        """
        return self.map_name_format.format(id=self.map.id)

    @property
    def qgis_map_path_prefix(self):
        """Returned QGIS map path prefix.

        based on map_name_format
        Path prefix: /usr/src/app/geonode/qgis_layer/map_1
        """
        return os.path.join(QGIS_LAYER_DIRECTORY, self.qgis_map_name)

    @property
    def qgis_project_path(self):
        """Returned QGIS Project path related with this map.

        based on map_name_format
        QGIS Project path: /usr/src/app/geonode/qgis_layer/map_1.qgs
        """
        return f'{self.qgis_map_path_prefix}.qgs'

    @property
    def cache_path(self):
        """Returned the location of tile cache for this layer.

        based on map_name_format
        QGIS cache path: /usr/src/app/geonode/qgis_tiles/map_1

        :return: Base path of layer cache
        :rtype: str
        """
        return os.path.join(QGIS_TILES_DIRECTORY, self.qgis_map_name)

    def get_self_resource(self):
        """Get associated resource base."""
        # Associate this model with resource
        try:
            return self.layer.get_self_resource()
        except Exception:
            return None

    class Meta:
        app_label = "qgis_server"
