# -*- coding: utf-8 -*-
import logging
import shutil
import os
from django.db.models import signals
from django.core.urlresolvers import reverse
from django.conf import settings

from geonode.qgis_server.models import QGISServerLayer
from geonode.base.models import ResourceBase, Link
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.layers.utils import create_thumbnail
from geonode.geoserver.helpers import http_client
from geonode.qgis_server.gis_tools import set_attributes


logger = logging.getLogger("geonode.qgis_server.signals")
QGIS_layer_directory = settings.QGIS_SERVER_CONFIG['layer_directory']


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
    # TODO
    # 1. Create or update associated QGISServerLayer [Done]
    # 2. Create Link for the tile and legend.
    logger.debug('QGIS Server Post Save')
    qgis_layer, created = QGISServerLayer.objects.get_or_create(layer=instance)
    # copy layer to QGIS Layer Directory
    geonode_layer_path = instance.get_base_file()[0].file.path
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
                    shutil.copy2(
                        base_filename + '.' + ext,
                        qgis_layer.base_layer_path + '.' + ext
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

    # Set Link for Download Raw in Zip File
    zip_download_url = reverse(
            'qgis-server-download-zip',
            kwargs={'layername': instance.name})
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

    tile_url = reverse(
            'qgis-server-tile',
            kwargs={'layername': instance.name, 'x': 5678, 'y':910, 'z': 1234})
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

    # Create legend link
    legend_url = reverse(
        'qgis-server-legend',
        kwargs={'layername': instance.name}
    )
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
    thumbnail_remote_url = settings.GEONODE_BASE_URL[:-1]
    thumbnail_remote_url += reverse(
        'qgis-server-thumbnail', kwargs={'layername': instance.name})
    logger.debug(thumbnail_remote_url)
    create_thumbnail(instance, thumbnail_remote_url, ogc_client=http_client)

    # Attributes
    set_attributes(instance)


def qgis_server_pre_save_maplayer(instance, sender, **kwargs):
    logger.debug('QGIS Server Pre Save Map Layer')
    try:
        layer = Layer.objects.get(typename=instance.name)
        if layer:
            instance.local = True
    except Layer.DoesNotExist:
        pass



def qgis_server_post_save_map(instance, sender, **kwargs):

    logger.debug('QGIS Server Post Save Map')


signals.post_save.connect(qgis_server_post_save, sender=ResourceBase)
signals.pre_save.connect(qgis_server_pre_save, sender=Layer)
signals.pre_delete.connect(qgis_server_pre_delete, sender=Layer)
signals.post_save.connect(qgis_server_post_save, sender=Layer)
signals.pre_save.connect(qgis_server_pre_save_maplayer, sender=MapLayer)
signals.post_save.connect(qgis_server_post_save_map, sender=Map)
signals.pre_delete.connect(qgis_server_layer_pre_delete, sender=QGISServerLayer)
