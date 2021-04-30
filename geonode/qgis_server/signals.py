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
import shutil

from osgeo import ogr, osr, gdal
from django.conf import settings
from django.urls import reverse
from django.db.models import signals
from django.dispatch import Signal
from requests.compat import urljoin

from geonode import qgis_server
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.compat import ensure_string
from geonode.maps.models import Map, MapLayer
from geonode.decorators import on_ogc_backend
from geonode.qgis_server.gis_tools import set_attributes
from geonode.qgis_server.helpers import create_qgis_project, get_model_path
from geonode.qgis_server.models import QGISServerLayer, QGISServerMap
from geonode.qgis_server.tasks.update import create_qgis_server_thumbnail
from geonode.qgis_server.xml_utilities import update_xml
from geonode.utils import check_ogc_backend, set_resource_default_links

logger = logging.getLogger("geonode.qgis_server.signals")

if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    QGIS_layer_directory = settings.QGIS_SERVER_CONFIG['layer_directory']

qgis_map_with_layers = Signal(providing_args=[])


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def qgis_server_layer_post_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage."""
    logger.debug('QGIS Server Layer Post Delete')
    instance.delete_qgis_layer()


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def qgis_server_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage."""
    # logger.debug('QGIS Server Pre Delete')
    # Deleting QGISServerLayer object happened on geonode level since it's
    # OneToOne relationship
    # Delete file is included when deleting the object.


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
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


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def qgis_server_post_save(instance, sender, **kwargs):
    """Save keywords to QGIS Server.

    The way keywords are implemented requires the layer to be saved to the
    database before accessing them.

    This hook also creates QGIS Project. Which is essentials for QGIS Server.
    There are also several Geonode Links generated, like thumbnail and legends

    :param instance: geonode Layer
    :type instance: Layer

    :param sender: geonode Layer type
    :type sender: type(Layer)
    """
    if not sender == Layer:
        return
    # TODO
    # 1. Create or update associated QGISServerLayer [Done]
    # 2. Create Link for the tile and legend.
    logger.debug('QGIS Server Post Save')

    # copy layer to QGIS Layer Directory
    try:
        geonode_layer_path = instance.get_base_file()[0].file.path
    except AttributeError:
        logger.debug('Layer does not have base file')
        return

    qgis_layer, created = QGISServerLayer.objects.get_or_create(
        layer=instance)
    logger.debug(f'Geonode Layer Path {geonode_layer_path}')

    base_filename, original_ext = os.path.splitext(geonode_layer_path)
    extensions = QGISServerLayer.accepted_format

    is_shapefile = False

    for ext in extensions:
        if os.path.exists(f"{base_filename}.{ext}"):
            is_shapefile = is_shapefile or ext == 'shp'
            try:
                if created:
                    # Assuming different layer has different filename because
                    # geonode rename it
                    shutil.copy2(
                        f"{base_filename}.{ext}",
                        QGIS_layer_directory
                    )
                    logger.debug('Create new basefile')
                else:
                    # If there is already a file, replace the old one
                    qgis_layer_base_filename = qgis_layer.qgis_layer_path_prefix
                    shutil.copy2(
                        f"{base_filename}.{ext}",
                        f"{qgis_layer_base_filename}.{ext}"
                    )
                    logger.debug('Overwrite existing basefile')
                logger.debug(
                    f"Copying {base_filename}.{ext} Success")
                logger.debug(f'Into {QGIS_layer_directory}')
            except IOError as e:
                logger.debug(
                    f"Copying {base_filename}.{ext} FAILED {e}")
    if created:
        # Only set when creating new QGISServerLayer Object
        geonode_filename = os.path.basename(geonode_layer_path)
        basename = os.path.splitext(geonode_filename)[0]
        qgis_layer.base_layer_path = os.path.join(
            QGIS_layer_directory,
            basename + original_ext  # Already with dot
        )
    qgis_layer.save()

    # refresh to get QGIS Layer
    instance.refresh_from_db()

    # Set layer crs
    try:
        if is_shapefile:
            dataset = ogr.Open(geonode_layer_path)
            layer = dataset.GetLayer()
            spatial_ref = layer.GetSpatialRef()
            srid = spatial_ref.GetAuthorityCode(None) if spatial_ref else None
            if srid:
                instance.srid = srid
        else:
            dataset = gdal.Open(geonode_layer_path)
            prj = dataset.GetProjection()
            srs = osr.SpatialReference(wkt=prj)
            srid = srs.GetAuthorityCode(None) if srs else None
            if srid:
                instance.srid = srid
    except Exception as e:
        logger.debug(f"Can't retrieve projection: {geonode_layer_path}")
        logger.exception(e)

    # Refresh and create the instance default links
    set_resource_default_links(instance, qgis_layer, is_shapefile=is_shapefile, original_ext=original_ext)

    # Create thumbnail
    overwrite = getattr(instance, 'overwrite', False)
    create_qgis_server_thumbnail.apply_async((
        get_model_path(instance),
        instance.id,
        overwrite
    ))

    # Attributes
    set_attributes(instance)

    # Update xml file

    # Read metadata from layer that InaSAFE use.
    # Some are not found: organisation, email, url
    try:
        new_values = {
            'date': instance.date.isoformat(),
            'abstract': instance.abstract,
            'title': instance.title,
            'license': instance.license_verbose,
        }
    except (TypeError, AttributeError):
        new_values = {}

    # Get the path of the metadata file
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    xml_file_path = f"{basename}.xml"
    if os.path.exists(xml_file_path):
        try:
            update_xml(xml_file_path, new_values)
        except (TypeError, AttributeError):
            pass

    # Also update xml in QGIS Server
    xml_file_path = f"{qgis_layer.qgis_layer_path_prefix}.xml"
    if os.path.exists(xml_file_path):
        try:
            update_xml(xml_file_path, new_values)
        except (TypeError, AttributeError):
            pass

    # Remove existing tile caches if overwrite
    if overwrite:
        tiles_directory = settings.QGIS_SERVER_CONFIG['tiles_directory']
        basename, _ = os.path.splitext(qgis_layer.base_layer_path)
        basename = os.path.basename(basename)
        tiles_cache_path = os.path.join(tiles_directory, basename)
        try:
            shutil.rmtree(tiles_cache_path)
        except OSError:
            # The path doesn't exists yet
            pass


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def qgis_server_pre_save_maplayer(instance, sender, **kwargs):
    logger.debug(f'QGIS Server Pre Save Map Layer {instance.name}')
    try:
        layer = Layer.objects.get(alternate=instance.name)
        if layer:
            instance.local = True
    except Layer.DoesNotExist:
        pass


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def qgis_server_post_save_map(instance, sender, **kwargs):
    """Post Save Map Hook for QGIS Server

    This hook will creates QGIS Project for a given map.
    This hook also generates thumbnail link.
    """
    logger.debug('QGIS Server Post Save Map custom')
    map_id = instance.id
    map_layers = MapLayer.objects.filter(map__id=map_id)

    # Geonode map supports local layers and remote layers
    # Remote layers were provided from other OGC services, so we don't
    # deal with it at the moment.
    local_layers = [_l for _l in map_layers if _l.local]

    layers = []
    for layer in local_layers:
        try:
            _l = Layer.objects.get(alternate=layer.name)
            if not _l.qgis_layer:
                raise QGISServerLayer.DoesNotExist
            layers.append(_l)
        except Layer.DoesNotExist:
            msg = f'No Layer found for typename: {layer.name}'
            logger.debug(msg)
        except QGISServerLayer.DoesNotExist:
            msg = f'No QGIS Server Layer found for typename: {layer.name}'
            logger.debug(msg)

    if not layers:
        # The signal is called too early, or the map has no layer yet.
        return

    base_url = settings.SITEURL
    # download map
    map_download_url = urljoin(
        base_url,
        reverse(
            'map_download',
            kwargs={'mapid': instance.id}))
    logger.debug(f'map_download_url: {map_download_url}')
    link_name = 'Download Data Layers'
    Link.objects.update_or_create(
        resource=instance.resourcebase_ptr,
        name=link_name,
        defaults=dict(
            extension='html',
            mime='text/html',
            url=map_download_url,
            link_type='data'
        )
    )
    # WMC map layer workspace
    ogc_wmc_url = urljoin(
        base_url,
        reverse(
            'map_wmc',
            kwargs={'mapid': instance.id}))
    logger.debug(f'wmc_download_url: {ogc_wmc_url}')
    link_name = 'Download Web Map Context'
    link_mime = 'application/xml'
    Link.objects.update_or_create(
        resource=instance.resourcebase_ptr,
        name=link_name,
        defaults=dict(
            extension='wmc.xml',
            mime=link_mime,
            url=ogc_wmc_url,
            link_type='data'
        )
    )

    # QLR map layer workspace
    ogc_qlr_url = urljoin(
        base_url,
        reverse(
            'map_download_qlr',
            kwargs={'mapid': instance.id}))
    logger.debug(f'qlr_map_download_url: {ogc_qlr_url}')
    link_name = 'Download QLR Layer file'
    link_mime = 'application/xml'
    Link.objects.update_or_create(
        resource=instance.resourcebase_ptr,
        name=link_name,
        defaults=dict(
            extension='qlr',
            mime=link_mime,
            url=ogc_qlr_url,
            link_type='data'
        )
    )

    # Set default bounding box based on all layers extents.
    # bbox format [xmin, xmax, ymin, ymax]
    bbox = instance.get_bbox_from_layers(instance.local_layers)
    instance.set_bounds_from_bbox(bbox, instance.srid)
    Map.objects.filter(id=map_id).update(
        bbox_x0=instance.bbox_x0,
        bbox_x1=instance.bbox_x1,
        bbox_y0=instance.bbox_y0,
        bbox_y1=instance.bbox_y1,
        srid=instance.srid,
        zoom=instance.zoom,
        center_x=instance.center_x,
        center_y=instance.center_y)

    # Check overwrite flag
    overwrite = getattr(instance, 'overwrite', False)

    # Create the QGIS Project
    qgis_map, created = QGISServerMap.objects.get_or_create(map=instance)

    # if it is newly created qgis_map, we should overwrite if existing files
    # exists.
    overwrite = created or overwrite
    response = create_qgis_project(
        layer=layers,
        qgis_project_path=qgis_map.qgis_project_path,
        overwrite=overwrite,
        internal=True)

    logger.debug(f'Create project url: {response.url}')
    logger.debug(
        f'Creating the QGIS Project : {qgis_map.qgis_project_path} -> {ensure_string(response.content)}')

    # Generate map thumbnail
    create_qgis_server_thumbnail.apply_async((
        get_model_path(instance),
        instance.id,
        True
    ))


@on_ogc_backend(qgis_server.BACKEND_PACKAGE)
def register_qgis_server_signals():
    """Helper function to register model signals."""
    # Do it only if qgis_server is being used
    logger.debug('Registering signals QGIS Server')
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
    signals.post_delete.connect(
        qgis_server_layer_post_delete,
        dispatch_uid='QGISServerLayer-qgis_server_layer_post_delete',
        sender=QGISServerLayer)
