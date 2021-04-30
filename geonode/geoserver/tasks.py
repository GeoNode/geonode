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
import shutil
import geoserver
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.contrib.staticfiles.templatetags import staticfiles

from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode.tasks.tasks import (
    AcquireLock,
    FaultTolerantTask)
from geonode import GeoNodeException
from geonode.upload import signals
from geonode.layers.models import (
    Layer, UploadSession)
from geonode.layers.utils import resolve_regions
from geonode.layers.metadata import set_metadata
from geonode.base.models import (
    ResourceBase,
    TopicCategory,
    SpatialRepresentationType)
from geonode.utils import (
    is_monochromatic_image,
    set_resource_default_links)
from geonode.geoserver.upload import geoserver_upload
from geonode.security.utils import spec_perms_is_empty
from geonode.catalogue.models import catalogue_post_save

from .helpers import (
    gs_catalog,
    ogc_server_settings,
    gs_slurp,
    set_styles,
    get_sld_for,
    set_layer_style,
    cascading_delete,
    fetch_gs_resource,
    create_gs_thumbnail,
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
            publishing = gs_catalog.get_layer(name)
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
                else:
                    sld = get_sld_for(gs_catalog, publishing)
            else:
                sld = get_sld_for(gs_catalog, publishing)

            style = None
            if sld is not None:
                try:
                    gs_catalog.create_style(
                        name,
                        sld,
                        raw=True,
                        workspace=settings.DEFAULT_WORKSPACE)
                    gs_catalog.reset()
                except geoserver.catalog.ConflictingDataError:
                    try:
                        gs_catalog.create_style(
                            f"{name}_layer",
                            sld,
                            raw=True,
                            workspace=settings.DEFAULT_WORKSPACE)
                        gs_catalog.reset()
                    except geoserver.catalog.ConflictingDataError as e:
                        msg = f'There was already a style named {name} in GeoServer, cannot overwrite: "{str(e)}"'
                        logger.error(msg)
                        e.args = (msg,)

                if style is None:
                    try:
                        style = gs_catalog.get_style(
                            name, workspace=settings.DEFAULT_WORKSPACE) or gs_catalog.get_style(name)
                    except Exception:
                        logger.warn('Could not retreive the Layer default Style name')
                        try:
                            style = gs_catalog.get_style(f"{name}_layer", workspace=settings.DEFAULT_WORKSPACE) or \
                                gs_catalog.get_style(f"{name}_layer")
                            logger.warn(
                                'No style could be created for the layer, falling back to POINT default one')
                        except Exception as e:
                            style = gs_catalog.get_style('point')
                            logger.warn(str(e))
                if style:
                    publishing.default_style = style
                    logger.debug('default style set to %s', name)
                    gs_catalog.save(publishing)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_finalize_upload',
    queue='geoserver.events',
    expires=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
    retry_backoff=True,
    retry_backoff_max=700,
    retry_jitter=True)
def geoserver_finalize_upload(
        self,
        import_id,
        instance_id,
        permissions,
        created,
        xml_file,
        sld_file,
        sld_uploaded,
        tempdir):
    """
    Finalize Layer and GeoServer configuration:
     - Sets Layer Metadata from XML and updates GeoServer Layer accordingly.
     - Sets Default Permissions
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    title = None
    abstract = None
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            from geonode.upload.models import Upload
            upload = Upload.objects.get(import_id=import_id)
            upload.layer = instance
            upload.save()

            # Sanity checks
            if isinstance(xml_file, list):
                if len(xml_file) > 0:
                    xml_file = xml_file[0]
                else:
                    xml_file = None
            elif not isinstance(xml_file, str):
                xml_file = None

            if xml_file and os.path.exists(xml_file) and os.access(xml_file, os.R_OK):
                instance.metadata_uploaded = True
                identifier, vals, regions, keywords = set_metadata(
                    open(xml_file).read())

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

                if vals:
                    title = vals.get('title', '')
                    abstract = vals.get('abstract', '')

                    # Updating GeoServer resource
                    gs_resource.title = title
                    gs_resource.abstract = abstract
                    gs_catalog.save(gs_resource)
                else:
                    vals = {}

                vals.update(dict(
                    uuid=instance.uuid,
                    name=instance.name,
                    owner=instance.owner,
                    store=gs_resource.store.name,
                    storeType=gs_resource.store.resource_type,
                    alternate=f"{gs_resource.store.workspace.name}:{gs_resource.name}",
                    title=gs_resource.title or gs_resource.store.name,
                    abstract=gs_resource.abstract or ''))

                instance.metadata_xml = xml_file
                regions_resolved, regions_unresolved = resolve_regions(regions)
                keywords.extend(regions_unresolved)

                # Assign the regions (needs to be done after saving)
                regions_resolved = list(set(regions_resolved))
                if regions_resolved:
                    if len(regions_resolved) > 0:
                        if not instance.regions:
                            instance.regions = regions_resolved
                        else:
                            instance.regions.clear()
                            instance.regions.add(*regions_resolved)

                # Assign the keywords (needs to be done after saving)
                keywords = list(set(keywords))
                if keywords:
                    if len(keywords) > 0:
                        if not instance.keywords:
                            instance.keywords = keywords
                        else:
                            instance.keywords.add(*keywords)

                # set model properties
                defaults = {}
                for key, value in vals.items():
                    if key == 'spatial_representation_type':
                        value = SpatialRepresentationType(identifier=value)
                    elif key == 'topic_category':
                        value, created = TopicCategory.objects.get_or_create(
                            identifier=value,
                            defaults={'description': '', 'gn_description': value})
                        key = 'category'
                        defaults[key] = value
                    else:
                        defaults[key] = value

                # Save all the modified information in the instance without triggering signals.
                try:
                    if not defaults.get('title', title):
                        defaults['title'] = instance.title or instance.name
                    if not defaults.get('abstract', abstract):
                        defaults['abstract'] = instance.abstract or ''

                    to_update = {}
                    to_update['charset'] = defaults.pop('charset', instance.charset)
                    to_update['storeType'] = defaults.pop('storeType', instance.storeType)
                    for _key in ('name', 'workspace', 'store', 'storeType', 'alternate', 'typename'):
                        if _key in defaults:
                            to_update[_key] = defaults.pop(_key)
                        else:
                            to_update[_key] = getattr(instance, _key)
                    to_update.update(defaults)

                    with transaction.atomic():
                        ResourceBase.objects.filter(
                            id=instance.resourcebase_ptr.id).update(
                            **defaults)
                        Layer.objects.filter(id=instance.id).update(**to_update)

                        # Refresh from DB
                        instance.refresh_from_db()
                except IntegrityError:
                    raise

            if sld_uploaded:
                geoserver_set_style(instance.id, sld_file)
            else:
                geoserver_create_style(instance.id, instance.name, sld_file, tempdir)

            logger.debug(f'Finalizing (permissions and notifications) Layer {instance}')
            instance.handle_moderated_uploads()

            if permissions is not None and not spec_perms_is_empty(permissions):
                logger.debug(f'Setting permissions {permissions} for {instance.name}')
                instance.set_permissions(permissions, created=created)

            try:
                # Update the upload sessions
                geonode_upload_sessions = UploadSession.objects.filter(resource=instance)
                geonode_upload_sessions.update(processed=False)
                instance.upload_session = geonode_upload_sessions.first()
            except Exception as e:
                logger.exception(e)

            instance.save(notify=not created)

            try:
                logger.debug(f"... Cleaning up the temporary folders {tempdir}")
                if tempdir and os.path.exists(tempdir):
                    shutil.rmtree(tempdir)
            finally:
                upload.complete = True
                upload.save()

            signals.upload_complete.send(sender=geoserver_finalize_upload, layer=instance)


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
            # Don't run this signal if is a Layer from a remote service
            if getattr(instance, "remote_service", None) is not None:
                return

            if instance.storeType == "remoteStore":
                return

            # Don't run this signal handler if it is a tile layer or a remote store (Service)
            #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
            if hasattr(instance, 'storeType') and getattr(instance, 'storeType') in ['tileStore', 'remoteStore']:
                return instance

            if isinstance(instance, ResourceBase):
                if hasattr(instance, 'layer'):
                    instance = instance.layer
                else:
                    return

            geonode_upload_sessions = UploadSession.objects.filter(resource=instance)
            geonode_upload_sessions.update(processed=False)

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

                """Get information from geoserver.

                The attributes retrieved include:

                * Bounding Box
                * SRID
                * Download links (WMS, WCS or WFS and KML)
                * Styles (SLD)
                """
                try:
                    # This is usually done in Layer.pre_save, however if the hooks
                    # are bypassed by custom create/updates we need to ensure the
                    # bbox is calculated properly.
                    bbox = gs_resource.native_bbox
                    instance.bbox_x0 = Decimal(bbox[0])
                    instance.bbox_x1 = Decimal(bbox[1])
                    instance.bbox_y0 = Decimal(bbox[2])
                    instance.bbox_y1 = Decimal(bbox[3])
                    instance.srid = gs_resource.projection
                except Exception as e:
                    logger.exception(e)
                if instance.bbox_x0 and not instance.srid:
                    # Guessing 'EPSG:4326' by default
                    instance.srid = 'EPSG:4326'
                elif not instance.bbox_x0:
                    raise GeoNodeException("Invalid Projection. Layer is missing CRS!")

                # Iterate over values from geoserver.
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
                    msg = f'Error while trying to save resource named {gs_resource} in GeoServer, try to use: "{str(e)}"'
                    e.args = (msg,)
                    logger.exception(e)

                # store the resource to avoid another geoserver call in the post_save
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

                if is_monochromatic_image(instance.thumbnail_url):
                    to_update['thumbnail_url'] = staticfiles.static(settings.MISSING_THUMBNAIL)

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

                        # Refresh from DB
                        instance.refresh_from_db()
                except Exception as e:
                    logger.exception(e)

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

                # Save layer attributes
                logger.debug(f"... Refresh GeoServer attributes list for Layer {instance.title}")
                try:
                    set_attributes_from_geoserver(instance)
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

                # Creating Layer Thumbnail by sending a signal
                from geonode.geoserver.signals import geoserver_post_save_complete
                geoserver_post_save_complete.send(
                    sender=instance.__class__, instance=instance, update_fields=['thumbnail_url'])
            try:
                geonode_upload_sessions = UploadSession.objects.filter(resource=instance)
                geonode_upload_sessions.update(processed=True)
            except Exception as e:
                logger.exception(e)

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
    retry_kwargs={'max_retries': 3, 'countdown': 10},
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
