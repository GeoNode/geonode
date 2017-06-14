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
from __future__ import absolute_import

import logging
import os
import shutil
import requests
from requests.compat import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import ObjectDoesNotExist, signals
from django.dispatch import Signal

from geonode import qgis_server
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.qgis_server.gis_tools import set_attributes
from geonode.qgis_server.helpers import tile_url
from geonode.qgis_server.models import QGISServerLayer
from geonode.qgis_server.tasks.update import create_qgis_server_thumbnail
from geonode.utils import check_ogc_backend
from geonode.qgis_server.xml_utilities import update_xml

logger = logging.getLogger("geonode.qgis_server.signals")

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    QGIS_layer_directory = settings.QGIS_SERVER_CONFIG['layer_directory']

qgis_map_with_layers = Signal(providing_args=[])


def qgis_server_layer_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage."""
    logger.debug('QGIS Server Layer Pre Delete')
    instance.delete_qgis_layer()


def qgis_server_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage."""
    # logger.debug('QGIS Server Pre Delete')
    # Deleting QGISServerLayer object happened on geonode level since it's
    # OneToOne relationship
    # Delete file is included when deleting the object.


def qgis_server_pre_save(instance, sender, **kwargs):
    """Send information to QGIS Server.

       The attributes sent include:

        * Title
        * Abstract
        * Name
        * Keywords
        * Metadata Links,
        * Point of Contact name and url
    """
    # logger.debug('QGIS Server Pre Save')


def qgis_server_post_save(instance, sender, **kwargs):
    """Save keywords to QGIS Server.

    The way keywords are implemented requires the layer to be saved to the
    database before accessing them.
    """
    if not sender == Layer:
        return
    # TODO
    # 1. Create or update associated QGISServerLayer [Done]
    # 2. Create Link for the tile and legend.
    logger.debug('QGIS Server Post Save')
    qgis_layer, created = QGISServerLayer.objects.get_or_create(
        layer=instance)
    # copy layer to QGIS Layer Directory
    try:
        geonode_layer_path = instance.get_base_file()[0].file.path
    except AttributeError:
        logger.debug('Layer does not have base file')
        return
    logger.debug('Geonode Layer Path %s' % geonode_layer_path)

    base_filename, original_ext = os.path.splitext(geonode_layer_path)
    extensions = QGISServerLayer.accepted_format

    is_shapefile = False

    for ext in extensions:
        if os.path.exists(base_filename + '.' + ext):
            is_shapefile = is_shapefile or ext == 'shp'
            try:
                if created:
                    # Assuming different layer has different filename because
                    # geonode rename it
                    shutil.copy2(
                        base_filename + '.' + ext,
                        QGIS_layer_directory
                    )
                else:
                    # If there is already a file, replace the old one
                    qgis_layer_base_filename, _ = os.path.splitext(
                        qgis_layer.base_layer_path)
                    shutil.copy2(
                        base_filename + '.' + ext,
                        qgis_layer_base_filename + '.' + ext
                    )
                logger.debug(
                    'Copying %s' % base_filename + '.' + ext + ' Success')
            except IOError as e:
                logger.debug(
                    'Copying %s' % base_filename + '.' + ext + ' FAILED ' + e)
    if created:
        # Only set when creating new QGISServerLayer Object
        geonode_filename = os.path.basename(geonode_layer_path)
        basename = os.path.splitext(geonode_filename)[0]
        qgis_layer.base_layer_path = os.path.join(
            QGIS_layer_directory,
            basename + original_ext  # Already with dot
        )
    qgis_layer.save()

    # base url for geonode
    base_url = settings.SITEURL

    # Set Link for Download Raw in Zip File
    zip_download_url = reverse(
        'qgis_server:download-zip', kwargs={'layername': instance.name})
    zip_download_url = urljoin(base_url, zip_download_url)
    logger.debug('zip_download_url: %s' % zip_download_url)
    if is_shapefile:
        link_name = 'Zipped Shapefile'
        link_mime = 'SHAPE-ZIP'
    else:
        link_name = 'Zipped All Files'
        link_mime = 'ZIP'

    # Zip file
    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=zip_download_url,
        defaults=dict(
            extension='zip',
            name=link_name,
            mime=link_mime,
            url=zip_download_url,
            link_type='data'
        )
    )

    # WMS link layer workspace
    ogc_wms_url = urljoin(
        settings.SITEURL,
        reverse(
            'qgis_server:layer-request', kwargs={'layername': instance.name}))
    ogc_wms_name = 'OGC WMS: %s Service' % instance.workspace
    ogc_wms_link_type = 'OGC:WMS'
    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=ogc_wms_url,
        link_type=ogc_wms_link_type,
        defaults=dict(
            extension='html',
            name=ogc_wms_name,
            url=ogc_wms_url,
            mime='text/html',
            link_type=ogc_wms_link_type
        )
    )

    if instance.is_vector():
        # WFS link layer workspace
        ogc_wfs_url = urljoin(
            settings.SITEURL,
            reverse(
                'qgis_server:layer-request',
                kwargs={'layername': instance.name}))
        ogc_wfs_name = 'OGC WFS: %s Service' % instance.workspace
        ogc_wfs_link_type = 'OGC:WFS'
        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=ogc_wfs_url,
            link_type=ogc_wfs_link_type,
            defaults=dict(
                extension='html',
                name=ogc_wfs_name,
                url=ogc_wfs_url,
                mime='text/html',
                link_type=ogc_wfs_link_type
            )
        )

    # Create the QGIS Project
    qgis_server = settings.QGIS_SERVER_CONFIG['qgis_server_url']
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    query_string = {
        'SERVICE': 'MAPCOMPOSITION',
        'PROJECT': '%s.qgs' % basename,
        'FILES': qgis_layer.base_layer_path,
        'NAMES': instance.name
    }
    response = requests.get(qgis_server, params=query_string)

    logger.debug('Creating the QGIS Project : %s' % response.url)
    if response.content != 'OK':
        logger.debug('Result : %s' % response.content)

    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=tile_url(instance.name),
        defaults=dict(
            extension='tiles',
            name="Tiles",
            mime='image/png',
            link_type='image'
        )
    )

    if original_ext.split('.')[-1] in QGISServerLayer.geotiff_format:
        # geotiff link
        geotiff_url = reverse(
            'qgis_server:geotiff', kwargs={'layername': instance.name})
        geotiff_url = urljoin(base_url, geotiff_url)
        logger.debug('geotif_url: %s' % geotiff_url)

        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=geotiff_url,
            defaults=dict(
                extension=original_ext.split('.')[-1],
                name="GeoTIFF",
                mime='image/tiff',
                link_type='image'
            )
        )

    # Create legend link
    legend_url = reverse(
        'qgis_server:legend',
        kwargs={'layername': instance.name}
    )
    legend_url = urljoin(base_url, legend_url)
    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=legend_url,
        defaults=dict(
            extension='png',
            name='Legend',
            url=legend_url,
            mime='image/png',
            link_type='image',
        )
    )

    # Create thumbnail
    create_qgis_server_thumbnail.delay(
        instance, overwrite=True)

    # Attributes
    set_attributes(instance)

    # Update xml file
    # Get the path of the metadata file
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    xml_file_path = basename + '.xml'
    if os.path.exists(xml_file_path):
        try:
            # Read metadata from layer that InaSAFE use.
            # Some are not found: organisation, email, url
            new_values = {
                'date': instance.date.isoformat(),
                'abstract': instance.abstract,
                'title': instance.title,
                'license': instance.license_verbose,
            }
            update_xml(xml_file_path, new_values)
        except (TypeError, AttributeError):
            pass


def qgis_server_pre_save_maplayer(instance, sender, **kwargs):
    logger.debug('QGIS Server Pre Save Map Layer %s' % instance.name)
    try:
        layer = Layer.objects.get(typename=instance.name)
        if layer:
            instance.local = True
    except Layer.DoesNotExist:
        pass


def qgis_server_post_save_map(instance, sender, **kwargs):
    logger.debug('QGIS Server Post Save Map custom')
    map_id = instance.id
    map_layers = MapLayer.objects.filter(map__id=map_id)
    local_layers = [l for l in map_layers if l.local]

    names = []
    files = []
    for layer in local_layers:
        l = Layer.objects.get(typename=layer.name)
        names.append(l.title)

        try:
            qgis_layer = QGISServerLayer.objects.get(layer=l)
            files.append(qgis_layer.base_layer_path)
        except ObjectDoesNotExist:
            msg = 'No QGIS Server Layer for existing layer %s' % l.title
            logger.debug(msg)

    if not files:
        # The signal is called to early, the map has not layer yet.
        return

    # Set bounding box based on all layers extents.
    bbox = instance.get_bbox_from_layers(instance.local_layers)
    instance.set_bounds_from_bbox(bbox)
    Map.objects.filter(id=map_id).update(
        bbox_x0=instance.bbox_x0,
        bbox_x1=instance.bbox_x1,
        bbox_y0=instance.bbox_y0,
        bbox_y1=instance.bbox_y1,
        zoom=instance.zoom,
        center_x=instance.center_x,
        center_y=instance.center_y)

    # Create the QGIS Project
    qgis_server = settings.QGIS_SERVER_CONFIG['qgis_server_url']
    project_path = os.path.join(QGIS_layer_directory, 'map_%s.qgs' % map_id)
    query_string = {
        'SERVICE': 'MAPCOMPOSITION',
        'PROJECT': project_path,
        'FILES': ';'.join(files),
        'NAMES': ';'.join(names),
        'OVERWRITE': 'true',
    }
    response = requests.get(qgis_server, params=query_string)

    logger.debug('Create project url: {url}'.format(url=response.url))
    logger.debug(
        'Creating the QGIS Project : %s -> %s' % (
            project_path, response.content))

    create_qgis_server_thumbnail.delay(
        instance, overwrite=True)


if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    logger.debug('Register signals QGIS Server')
    signals.pre_save.connect(
        qgis_server_pre_save,
        dispatch_uid='Layer-qgis_server_pre_save',
        sender=Layer)
    signals.pre_delete.connect(
        qgis_server_pre_delete,
        dispatch_uid='Layer-qgis_server_pre_delete',
        sender=Layer)
    signals.post_save.connect(
        qgis_server_post_save,
        dispatch_uid='Layer-qgis_server_post_save',
        sender=Layer)
    signals.pre_save.connect(
        qgis_server_pre_save_maplayer,
        dispatch_uid='MapLayer-qgis_server_pre_save_maplayer',
        sender=MapLayer)
    signals.post_save.connect(
        qgis_server_post_save_map,
        dispatch_uid='Map-qgis_server_post_save_map',
        sender=Map)
    signals.pre_delete.connect(
        qgis_server_layer_pre_delete,
        dispatch_uid='QGISServerLayer-qgis_server_layer_pre_delete',
        sender=QGISServerLayer)
