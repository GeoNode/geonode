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
import shutil
import os
from urllib2 import urlopen, quote
from urlparse import urljoin

from django.db.models import signals, ObjectDoesNotExist
from django.dispatch import Signal
from django.core.urlresolvers import reverse
from django.conf import settings

from geonode.qgis_server.models import QGISServerLayer
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.qgis_server.tasks.update import create_qgis_server_thumbnail
from geonode.geoserver.helpers import http_client
from geonode.qgis_server.gis_tools import set_attributes


logger = logging.getLogger("geonode.qgis_server.signals")
QGIS_layer_directory = settings.QGIS_SERVER_CONFIG['layer_directory']

qgis_map_with_layers = Signal(providing_args=[])


def qgis_server_layer_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage
    """
    logger.debug('QGIS Server Layer Pre Delete')
    instance.delete_qgis_layer()


def qgis_server_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage
    """
    logger.debug('QGIS Server Pre Delete')
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
    logger.debug('QGIS Server Pre Save')


def qgis_server_post_save(instance, sender, **kwargs):
    """Save keywords to QGIS Server

       The way keywords are implemented requires the layer
       to be saved to the database before accessing them.
    """
    if not sender == Layer:
        return
    # TODO
    # 1. Create or update associated QGISServerLayer [Done]
    # 2. Create Link for the tile and legend.
    logger.debug('QGIS Server Post Save')
    qgis_layer, created = QGISServerLayer.objects.get_or_create(layer=instance)
    # copy layer to QGIS Layer Directory
    try:
        geonode_layer_path = instance.get_base_file()[0].file.path
    except AttributeError:
        logger.debug('Layer does not have base file')
        return
    logger.debug('Geonode Layer Path %s' % geonode_layer_path)

    base_filename, original_ext = os.path.splitext(geonode_layer_path)
    extensions = QGISServerLayer.accepted_format

    for ext in extensions:
        if os.path.exists(base_filename + '.' + ext):
            logger.debug('Copying %s' % base_filename + '.' + ext)
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
                logger.debug('Success')
            except IOError as e:
                logger.debug('Error copying file. %s' % e)
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
            'qgis-server-download-zip',
            kwargs={'layername': instance.name})
    zip_download_url = urljoin(base_url, zip_download_url)
    logger.debug('zip_download_url: %s' % zip_download_url)
    Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=zip_download_url,
            defaults=dict(
                        extension='zip',
                        name='Zipped Shapefile',
                        mime='SHAPE-ZIP',
                        url=zip_download_url,
                        link_type='data'
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

    url = qgis_server + '?'
    for param, value in query_string.iteritems():
        url += param + '=' + value + '&'
    url = url[:-1]

    data = urlopen(url).read()
    logger.debug('Creating the QGIS Project : %s' % url)
    if data != 'OK':
        logger.debug('Result : %s' % data)

    tile_url = reverse(
        'qgis-server-tile',
        kwargs={
            'layername': instance.name,
            'x': 5678,
            'y': 910,
            'z': 1234
        })
    tile_url = urljoin(base_url, tile_url)
    logger.debug('tile_url: %s' % tile_url)
    tile_url = tile_url.replace('1234/5678/910', '{z}/{x}/{y}')
    logger.debug('tile_url: %s' % tile_url)

    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=tile_url,
        defaults=dict(
            extension='tiles',
            name="Tiles",
            mime='image/png',
            link_type='image'
        )
    )

    # geotiff link
    geotiff_url = reverse(
        'qgis-server-geotiff', kwargs={'layername': instance.name})
    geotiff_url = urljoin(base_url, geotiff_url)
    logger.debug('geotif_url: %s' % geotiff_url)

    Link.objects.get_or_create(
        resource=instance.resourcebase_ptr,
        url=geotiff_url,
        defaults=dict(
            extension='tif',
            name="GeoTIFF",
            mime='image/tif',
            link_type='image'
        )
    )

    # Create legend link
    legend_url = reverse(
        'qgis-server-legend',
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
    thumbnail_remote_url = reverse(
        'qgis-server-thumbnail', kwargs={'layername': instance.name})
    thumbnail_remote_url = urljoin(base_url, thumbnail_remote_url)
    logger.debug(thumbnail_remote_url)

    create_qgis_server_thumbnail.delay(
        instance, thumbnail_remote_url, ogc_client=http_client)

    # Attributes
    set_attributes(instance)


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

    # Create the QGIS Project
    qgis_server = settings.QGIS_SERVER_CONFIG['qgis_server_url']
    project_path = os.path.join(QGIS_layer_directory, 'map_%s.qgs' % map_id)
    query_string = {
        'SERVICE': 'MAPCOMPOSITION',
        'PROJECT': project_path,
        'FILES': ';'.join(files),
        'NAMES': ';'.join(names)
    }

    url = qgis_server + '?'
    for param, value in query_string.iteritems():
        url += param + '=' + quote(value) + '&'
    url = url[:-1]

    data = urlopen(url).read()
    logger.debug('Creating the QGIS Project : %s -> %s' % (project_path, data))

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
