# -*- coding: utf-8 -*-
import logging
import shutil
import os
from django.db.models import signals

from django.conf import settings

from geonode.qgis_server.models import QGISServerLayer
from geonode.base.models import ResourceBase
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer


logger = logging.getLogger("geonode.qgis_server.signals")


def qgis_server_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage
    """
    logger.debug('QGIS Server Pre Delete')


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
                        settings.QGIS_SERVER_CONFIG['layer_directory']
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
        qgis_layer.base_layer_path = os.path.join(
            settings.QGIS_SERVER_CONFIG['layer_directory'],
            base_filename + '.' + original_ext
        )
    qgis_layer.save()

def qgis_server_pre_save_maplayer(instance, sender, **kwargs):
    logger.debug('QGIS Server Pre Save Map Layer')


def qgis_server_post_save_map(instance, sender, **kwargs):

    logger.debug('QGIS Server Post Save Map')


signals.post_save.connect(qgis_server_post_save, sender=ResourceBase)
signals.pre_save.connect(qgis_server_pre_save, sender=Layer)
signals.pre_delete.connect(qgis_server_pre_delete, sender=Layer)
signals.post_save.connect(qgis_server_post_save, sender=Layer)
signals.pre_save.connect(qgis_server_pre_save_maplayer, sender=MapLayer)
signals.post_save.connect(qgis_server_post_save_map, sender=Map)
