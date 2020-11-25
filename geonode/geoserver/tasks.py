# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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
from time import sleep
from django.conf import settings
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode import GeoNodeException
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase
from geonode.utils import set_resource_default_links
from geonode.geoserver.upload import geoserver_upload
from geonode.catalogue.models import catalogue_post_save

from geonode.geoserver.helpers import (
    gs_catalog,
    ogc_server_settings,
    set_styles,
    create_gs_thumbnail,
    set_attributes_from_geoserver,
    _stylefilterparams_geowebcache_layer,
    _invalidate_geowebcache_layer)

from .helpers import gs_slurp, cascading_delete

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_update_layers',
    queue='update',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def geoserver_update_layers(self, *args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_post_save_layers',
    queue='update',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def geoserver_post_save_layers(
        self,
        instance_id,
        *args, **kwargs):
    """
    Runs update layers.
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.error(f"Layer id {instance_id} does not exist yet!")
        return

    # Don't run this signal if is a Layer from a remote service
    if getattr(instance, "remote_service", None) is not None:
        return

    # Don't run this signal handler if it is a tile layer or a remote store (Service)
    #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
    if hasattr(instance, 'storeType') and getattr(instance, 'storeType') in ['tileStore', 'remoteStore']:
        return instance

    gs_resource = None
    values = None
    _tries = 0
    _max_tries = getattr(ogc_server_settings, "MAX_RETRIES", 2)

    # If the store in None then it's a new instance from an upload,
    # only in this case run the geoserver_upload method
    if not instance.store or getattr(instance, 'overwrite', False):
        base_file, info = instance.get_base_file()

        # There is no need to process it if there is no file.
        if base_file is None:
            return
        gs_name, workspace, values, gs_resource = geoserver_upload(
            instance,
            base_file.file.path,
            instance.owner,
            instance.name,
            overwrite=True,
            title=instance.title,
            abstract=instance.abstract,
            charset=instance.charset
        )

    def fetch_gs_resource(values, tries):
        try:
            gs_resource = gs_catalog.get_resource(
                name=instance.name,
                store=instance.store,
                workspace=instance.workspace)
        except Exception:
            try:
                gs_resource = gs_catalog.get_resource(
                    name=instance.alternate,
                    store=instance.store,
                    workspace=instance.workspace)
            except Exception:
                try:
                    gs_resource = gs_catalog.get_resource(
                        name=instance.alternate or instance.typename)
                except Exception:
                    gs_resource = None
        if gs_resource:
            if values:
                gs_resource.title = values.get('title', '')
                gs_resource.abstract = values.get('abstract', '')
            else:
                values = {}
            values.update(dict(store=gs_resource.store.name,
                               storeType=gs_resource.store.resource_type,
                               alternate=gs_resource.store.workspace.name + ':' + gs_resource.name,
                               title=gs_resource.title or gs_resource.store.name,
                               abstract=gs_resource.abstract or '',
                               owner=instance.owner))
        else:
            msg = "There isn't a geoserver resource for this layer: %s" % instance.name
            logger.exception(msg)
            if tries >= _max_tries:
                # raise GeoNodeException(msg)
                return (values, None)
            gs_resource = None
            sleep(5.00)
        return (values, gs_resource)

    values, gs_resource = fetch_gs_resource(values, _tries)
    while not gs_resource and _tries < _max_tries:
        values, gs_resource = fetch_gs_resource(values, _tries)
        _tries += 1

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.mime, link.name, link.url))

    if gs_resource:
        logger.debug("Found geoserver resource for this layer: %s" % instance.name)
        gs_resource.metadata_links = metadata_links

        # Update Attribution link
        if instance.poc:
            # gsconfig now utilizes an attribution dictionary
            gs_resource.attribution = {'title': str(instance.poc),
                                       'width': None,
                                       'height': None,
                                       'href': None,
                                       'url': None,
                                       'type': None}
            profile = get_user_model().objects.get(username=instance.poc.username)
            site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
            gs_resource.attribution_link = site_url + profile.get_absolute_url()
    else:
        msg = "There isn't a geoserver resource for this layer: %s" % instance.name
        logger.warn(msg)

    if isinstance(instance, ResourceBase):
        if hasattr(instance, 'layer'):
            instance = instance.layer
        else:
            return

    # Save layer attributes
    set_attributes_from_geoserver(instance)

    # Save layer styles
    set_styles(instance, gs_catalog)

    # Invalidate GeoWebCache for the updated resource
    try:
        _stylefilterparams_geowebcache_layer(instance.alternate)
        _invalidate_geowebcache_layer(instance.alternate)
    except Exception:
        pass

    if instance.storeType == "remoteStore":
        return

    if gs_resource:
        """Get information from geoserver.

           The attributes retrieved include:

           * Bounding Box
           * SRID
           * Download links (WMS, WCS or WFS and KML)
           * Styles (SLD)
        """
        instance.workspace = gs_resource.store.workspace.name
        instance.store = gs_resource.store.name

        try:
            # This is usually done in Layer.pre_save, however if the hooks
            # are bypassed by custom create/updates we need to ensure the
            # bbox is calculated properly.
            bbox = gs_resource.native_bbox

            # Set bounding box values
            instance.bbox_x0 = bbox[0]
            instance.bbox_x1 = bbox[1]
            instance.bbox_y0 = bbox[2]
            instance.bbox_y1 = bbox[3]
            instance.srid = bbox[4]
        except Exception as e:
            logger.exception(e)

    # Iterate over values from geoserver.
    if gs_resource:
        for key in ['alternate', 'store', 'storeType']:
            # attr_name = key if 'typename' not in key else 'alternate'
            # print attr_name
            setattr(instance, key, values[key])

        try:
            if settings.RESOURCE_PUBLISHING:
                if instance.is_published != gs_resource.advertised:
                    gs_resource.advertised = 'true'

            if not settings.FREETEXT_KEYWORDS_READONLY:
                # AF: Warning - this won't allow people to have empty keywords on GeoNode
                if len(instance.keyword_list()) == 0 and gs_resource.keywords:
                    for keyword in gs_resource.keywords:
                        if keyword not in instance.keyword_list():
                            instance.keywords.add(keyword)

            if any(instance.keyword_list()):
                keywords = instance.keyword_list()
                gs_resource.keywords = [kw for kw in list(set(keywords))]

            # gs_resource should only be called if
            # ogc_server_settings.BACKEND_WRITE_ENABLED == True
            if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                gs_catalog.save(gs_resource)
        except Exception as e:
            msg = ('Error while trying to save resource named %s in GeoServer, '
                   'try to use: "%s"' % (gs_resource, str(e)))
            e.args = (msg,)
            logger.exception(e)

    if instance.srid:
        instance.srid_url = "http://www.spatialreference.org/ref/" + \
            instance.srid.replace(':', '/').lower() + "/"
    elif instance.bbox_x0 and instance.bbox_x1 and instance.bbox_y0 and instance.bbox_y1:
        # Guessing 'EPSG:4326' by default
        instance.srid = 'EPSG:4326'
    else:
        raise GeoNodeException("Invalid Projection. Layer is missing CRS!")

    to_update = {
        'title': instance.title or instance.name,
        'abstract': instance.abstract or "",
        'alternate': instance.alternate,
        'bbox_x0': instance.bbox_x0,
        'bbox_x1': instance.bbox_x1,
        'bbox_y0': instance.bbox_y0,
        'bbox_y1': instance.bbox_y1,
        'srid': instance.srid
    }

    # Save all the modified information in the instance without triggering signals.
    try:
        with transaction.atomic():
            ResourceBase.objects.filter(
                id=instance.resourcebase_ptr.id).update(
                **to_update)

            # to_update['name'] = instance.name,
            to_update['workspace'] = instance.workspace
            to_update['store'] = instance.store
            to_update['storeType'] = instance.storeType
            to_update['typename'] = instance.alternate

            Layer.objects.filter(id=instance.id).update(**to_update)

            # Refresh from DB
            instance.refresh_from_db()
    except IntegrityError:
        raise

    # Updating the Catalogue
    catalogue_post_save(instance=instance, sender=instance.__class__)

    # store the resource to avoid another geoserver call in the post_save
    if gs_resource:
        instance.gs_resource = gs_resource

        # some thumbnail generators will update thumbnail_url.  If so, don't
        # immediately re-generate the thumbnail here.  use layer#save(update_fields=['thumbnail_url'])
        logger.debug("... Creating Default Resource Links for Layer [%s]" % (instance.alternate))
        set_resource_default_links(instance, instance, prune=True)

        if 'update_fields' in kwargs and kwargs['update_fields'] is not None and \
                'thumbnail_url' in kwargs['update_fields']:
            logger.debug("... Creating Thumbnail for Layer [%s]" % (instance.alternate))
            create_gs_thumbnail(instance, overwrite=True)

    # Updating HAYSTACK Indexes if needed
    if settings.HAYSTACK_SEARCH:
        from django.core.management import call_command
        call_command('update_index')


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_cascading_delete',
    queue='cleanup',
    countdown=60,
    # expires=120,
    acks_late=True,
    retry=True,
    retry_policy={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    })
def geoserver_cascading_delete(self, *args, **kwargs):
    """
    Runs cascading_delete.
    """
    return cascading_delete(*args, **kwargs)
