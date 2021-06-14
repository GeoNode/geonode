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
import os
import re

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils.translation import ugettext_lazy as _
from django.templatetags.static import static

from celery import shared_task
from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode.tasks.tasks import (
    AcquireLock,
    FaultTolerantTask)
from geonode import GeoNodeException
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase
from geonode.utils import (
    is_monochromatic_image,
    set_resource_default_links)
from geonode.geoserver.upload import geoserver_upload
from geonode.catalogue.models import catalogue_post_save
from geonode.geoserver.helpers import get_layer_storetype

from .security import sync_resources_with_guardian
from .helpers import (
    gs_slurp,
    gs_catalog,
    set_styles,
    get_sld_for,
    set_layer_style,
    cascading_delete,
    fetch_gs_resource,
    create_gs_thumbnail,
    ogc_server_settings,
    set_attributes_from_geoserver,
    _invalidate_geowebcache_layer,
    _stylefilterparams_geowebcache_layer)

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_update_layers',
    queue='geoserver.catalog',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_update_layers(self, *args, **kwargs):
    """
    Runs update layers.
    """
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            return gs_slurp(*args, **kwargs)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_set_style',
    queue='geoserver.catalog',
    expires=30,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_set_style(
        self,
        instance_id,
        base_file):
    """
    Sets styles from SLD file.
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                sld = open(base_file, "rb").read()
                set_layer_style(
                    instance,
                    instance.alternate,
                    sld,
                    base_file=base_file)
            except Exception as e:
                logger.exception(e)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_create_style',
    queue='geoserver.catalog',
    expires=30,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_create_style(
        self,
        instance_id,
        name,
        sld_file,
        tempdir):
    """
    Sets or create styles from Upload Session.
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True and instance:
            if sld_file and os.path.exists(sld_file) and os.access(sld_file, os.R_OK):
                f = None
                if os.path.isfile(sld_file):
                    try:
                        f = open(sld_file, 'r')
                    except Exception:
                        pass
                elif tempdir and os.path.exists(tempdir):
                    if os.path.isfile(os.path.join(tempdir, sld_file)):
                        try:
                            f = open(os.path.join(tempdir, sld_file), 'r')
                        except Exception:
                            pass
                if f:
                    sld = f.read()
                    f.close()
                    if not gs_catalog.get_style(name=name, workspace=settings.DEFAULT_WORKSPACE):
                        style = gs_catalog.create_style(
                            name,
                            sld,
                            raw=True,
                            workspace=settings.DEFAULT_WORKSPACE)
                        gs_layer = gs_catalog.get_layer(name)
                        _default_style = gs_layer.default_style
                        gs_layer.default_style = style
                        gs_catalog.save(gs_layer)
                        set_styles(instance, gs_catalog)
                        try:
                            gs_catalog.delete(_default_style)
                        except Exception as e:
                            logger.exception(e)
                else:
                    get_sld_for(gs_catalog, instance)
            else:
                get_sld_for(gs_catalog, instance)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_post_save_layers',
    queue='geoserver.catalog',
    expires=3600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
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
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            if isinstance(instance, ResourceBase):
                if hasattr(instance, 'layer'):
                    instance = instance.layer
                else:
                    return instance

            # Save layer attributes
            logger.debug(f"... Refresh GeoServer attributes list for Layer {instance.title}")
            try:
                set_attributes_from_geoserver(instance)
            except Exception as e:
                logger.exception(e)

            # Don't run this signal handler if it is a tile layer or a remote store (Service)
            #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
            if hasattr(instance, 'storeType') and getattr(instance, 'storeType') in ['tileStore', 'remote']:
                # # Creating Layer Thumbnail by sending a signal
                # geoserver_post_save_complete.send(
                #     sender=instance.__class__, instance=instance, update_fields=['thumbnail_url'])
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

            values, gs_resource = fetch_gs_resource(instance, values, _tries)
            while not gs_resource and _tries < _max_tries:
                values, gs_resource = fetch_gs_resource(instance, values, _tries)
                _tries += 1

            # Get metadata links
            metadata_links = []
            for link in instance.link_set.metadata():
                metadata_links.append((link.mime, link.name, link.url))

            if gs_resource:
                logger.debug(f"Found geoserver resource for this layer: {instance.name}")
                gs_resource.metadata_links = metadata_links
                instance.gs_resource = gs_resource

                # Update Attribution link
                if instance.poc:
                    # gsconfig now utilizes an attribution dictionary
                    gs_resource.attribution = {
                        'title': str(instance.poc),
                        'width': None,
                        'height': None,
                        'href': None,
                        'url': None,
                        'type': None}
                    profile = get_user_model().objects.get(username=instance.poc.username)
                    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
                    gs_resource.attribution_link = site_url + profile.get_absolute_url()

                # Iterate over values from geoserver.
                for key in ['alternate', 'store', 'storeType']:
                    # attr_name = key if 'typename' not in key else 'alternate'
                    # print attr_name
                    setattr(instance, key, get_layer_storetype(values[key]))

                try:
                    if settings.RESOURCE_PUBLISHING:
                        if instance.is_published != gs_resource.advertised:
                            gs_resource.advertised = 'true'

                    if any(instance.keyword_list()):
                        keywords = gs_resource.keywords + instance.keyword_list()
                        gs_resource.keywords = list(set(keywords))

                    # gs_resource should only be called if
                    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
                    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                        gs_catalog.save(gs_resource)
                except Exception as e:
                    msg = (f'Error while trying to save resource named {gs_resource} in GeoServer, '
                           f'try to use: "{e}"')
                    e.args = (msg,)
                    logger.exception(e)

                # store the resource to avoid another geoserver call in the post_save
                """Get information from geoserver.
                The attributes retrieved include:
                * Bounding Box
                * SRID
                """
                try:
                    # This is usually done in Layer.pre_save, however if the hooks
                    # are bypassed by custom create/updates we need to ensure the
                    # bbox is calculated properly.
                    srid = gs_resource.projection
                    bbox = gs_resource.native_bbox
                    instance.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], srid)
                except Exception as e:
                    logger.exception(e)
                    srid = instance.srid
                    bbox = instance.bbox

                if instance.srid:
                    instance.srid_url = f"http://www.spatialreference.org/ref/{instance.srid.replace(':', '/').lower()}/"
                elif instance.bbox_polygon is not None:
                    # Guessing 'EPSG:4326' by default
                    instance.srid = 'EPSG:4326'
                else:
                    raise GeoNodeException(_("Invalid Projection. Layer is missing CRS!"))

                to_update = {
                    'title': instance.title or instance.name,
                    'abstract': instance.abstract or "",
                    'alternate': instance.alternate
                }

                if is_monochromatic_image(instance.thumbnail_url):
                    to_update['thumbnail_url'] = static(settings.MISSING_THUMBNAIL)

                # Save all the modified information in the instance without triggering signals.
                try:
                    with transaction.atomic():
                        ResourceBase.objects.filter(
                            id=instance.resourcebase_ptr.id).update(
                            **to_update)

                        # to_update['name'] = instance.name,
                        to_update['workspace'] = gs_resource.store.workspace.name
                        to_update['store'] = gs_resource.store.name
                        to_update['storeType'] = instance.storeType
                        to_update['typename'] = instance.alternate

                        Layer.objects.filter(id=instance.id).update(**to_update)

                        # Dealing with the BBOX: this is a trick to let GeoDjango storing original coordinates
                        instance.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], 'EPSG:4326')
                        Layer.objects.filter(id=instance.id).update(
                            bbox_polygon=instance.bbox_polygon, srid=srid)

                        # Refresh from DB
                        instance.refresh_from_db()
                except Exception as e:
                    logger.exception(e)

                try:
                    with transaction.atomic():
                        match = re.match(r'^(EPSG:)?(?P<srid>\d{4,6})$', str(srid))
                        instance.bbox_polygon.srid = int(match.group('srid')) if match else 4326
                        Layer.objects.filter(id=instance.id).update(
                            ll_bbox_polygon=instance.bbox_polygon, srid=srid)

                        # Refresh from DB
                        instance.refresh_from_db()
                except Exception as e:
                    logger.warning(e)
                    try:
                        with transaction.atomic():
                            instance.bbox_polygon.srid = 4326
                            Layer.objects.filter(id=instance.id).update(
                                ll_bbox_polygon=instance.bbox_polygon, srid=srid)

                            # Refresh from DB
                            instance.refresh_from_db()
                    except Exception as e:
                        logger.warning(e)

                # Refreshing CSW records
                logger.debug(f"... Updating the Catalogue entries for Layer {instance.title}")
                try:
                    catalogue_post_save(instance=instance, sender=instance.__class__)
                except Exception as e:
                    logger.exception(e)

                # Refreshing layer links
                logger.debug(f"... Creating Default Resource Links for Layer {instance.title}")
                try:
                    set_resource_default_links(instance, instance, prune=True)
                except Exception as e:
                    logger.exception(e)

                # Save layer styles
                logger.debug(f"... Refresh Legend links for Layer {instance.title}")
                try:
                    set_styles(instance, gs_catalog)
                except Exception as e:
                    logger.exception(e)

                # Invalidate GeoWebCache for the updated resource
                try:
                    _stylefilterparams_geowebcache_layer(instance.alternate)
                    _invalidate_geowebcache_layer(instance.alternate)
                except Exception:
                    pass

                # # Creating Layer Thumbnail by sending a signal
                # geoserver_post_save_complete.send(
                #     sender=instance.__class__, instance=instance, update_fields=['thumbnail_url'])

            # Updating HAYSTACK Indexes if needed
            if settings.HAYSTACK_SEARCH:
                call_command('update_index')


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_create_thumbnail',
    queue='geoserver.events',
    expires=30,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_create_thumbnail(self, instance_id, overwrite=True, check_bbox=True):
    """
    Runs create_gs_thumbnail.
    """
    instance = None
    try:
        instance = ResourceBase.objects.get(id=instance_id).get_real_instance()
    except Exception:
        logger.error(f"Resource id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                create_gs_thumbnail(instance, overwrite=overwrite, check_bbox=check_bbox)
                logger.debug(f"... Created Thumbnail for Layer {instance.title}")
            except Exception as e:
                geoserver_create_thumbnail.retry(exc=e)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_cascading_delete',
    queue='cleanup',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 1, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_cascading_delete(self, *args, **kwargs):
    """
    Runs cascading_delete.
    """
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            return cascading_delete(*args, **kwargs)


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_delete_map',
    queue='cleanup',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 1, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_delete_map(self, object_id):
    """
    Deletes a map and the associated map layers.
    """
    from geonode.maps.models import Map
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                map_obj = Map.objects.get(id=object_id)
            except Map.DoesNotExist:
                return

            map_obj.layer_set.all().delete()
            map_obj.delete()


@shared_task(
    bind=True,
    name='geonode.security.tasks.synch_guardian',
    queue='security',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def synch_guardian():
    """
    Sync resources with Guardian and clear their dirty state
    """
    if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        sync_resources_with_guardian()
