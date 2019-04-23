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

import errno
import logging

from django.conf import settings
from django.forms.models import model_to_dict

# use different name to avoid module clash
from . import BACKEND_PACKAGE
from geonode import GeoNodeException
from geonode.utils import set_resource_default_links
from geonode.decorators import on_ogc_backend
from geonode.geoserver.upload import geoserver_upload
from geonode.geoserver.helpers import (cascading_delete,
                                       set_attributes_from_geoserver,
                                       set_styles,
                                       set_layer_style,
                                       gs_catalog,
                                       ogc_server_settings,
                                       create_gs_thumbnail,
                                       _stylefilterparams_geowebcache_layer,
                                       _invalidate_geowebcache_layer)
from geonode.base.models import ResourceBase
from geonode.people.models import Profile
from geonode.layers.models import Layer
from geonode.social.signals import json_serializer_producer
from geonode.catalogue.models import catalogue_post_save
from geonode.services.enumerations import CASCADED

import geoserver
from geoserver.layer import Layer as GsLayer

logger = logging.getLogger("geonode.geoserver.signals")


def geoserver_delete(typename):
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        cascading_delete(gs_catalog, typename)


def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        if instance.remote_service is None or instance.remote_service.method == CASCADED:
            if instance.alternate:
                cascading_delete(gs_catalog, instance.alternate)


def geoserver_pre_save(*args, **kwargs):
    # nothing to do here, processing is pushed to post-save
    pass


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_post_save(instance, sender, **kwargs):
    from geonode.messaging import producer
    # this is attached to various models, (ResourceBase, Document)
    # so we should select what will be handled here
    if isinstance(instance, Layer):
        instance_dict = model_to_dict(instance)
        payload = json_serializer_producer(instance_dict)
        producer.geoserver_upload_layer(payload)

        if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            instance.set_dirty_state()

        if instance.storeType != 'remoteStore':
            logger.info("... Creating Thumbnail for Layer [%s]" % (instance.alternate))
            try:
                create_gs_thumbnail(instance, overwrite=True, check_bbox=True)
            except BaseException:
                logger.warn("!WARNING! - Failure while Creating Thumbnail for Layer [%s]" % (instance.alternate))


def geoserver_post_save_local(instance, *args, **kwargs):
    """Send information to geoserver.

       The attributes sent include:

        * Title
        * Abstract
        * Name
        * Keywords
        * Metadata Links,
        * Point of Contact name and url
    """
    # Don't run this signal if is a Layer from a remote service
    if getattr(instance, "remote_service", None) is not None:
        return

    # Don't run this signal handler if it is a tile layer or a remote store (Service)
    #    Currently only gpkg files containing tiles will have this type & will be served via MapProxy.
    if hasattr(instance, 'storeType') and getattr(instance, 'storeType') in ['tileStore', 'remoteStore']:
        return instance

    gs_resource = None
    values = None

    # If the store in None then it's a new instance from an upload,
    # only in this case run the geoserver_upload method
    if not instance.store or getattr(instance, 'overwrite', False):
        base_file, info = instance.get_base_file()

        # There is no need to process it if there is not file.
        if base_file is None:
            return
        gs_name, workspace, values, gs_resource = geoserver_upload(instance,
                                                                   base_file.file.path,
                                                                   instance.owner,
                                                                   instance.name,
                                                                   overwrite=True,
                                                                   title=instance.title,
                                                                   abstract=instance.abstract,
                                                                   # keywords=instance.keywords,
                                                                   charset=instance.charset)

    if not gs_resource:
        gs_resource = gs_catalog.get_resource(
            instance.name,
            store=instance.store,
            workspace=instance.workspace)
        if not gs_resource:
            gs_resource = gs_catalog.get_resource(instance.alternate)

    if gs_resource:
        gs_resource.title = instance.title or ""
        gs_resource.abstract = instance.abstract or ""
        gs_resource.name = instance.name or ""

        if not values:
            values = dict(store=gs_resource.store.name,
                          storeType=gs_resource.store.resource_type,
                          alternate=gs_resource.store.workspace.name + ':' + gs_resource.name,
                          title=gs_resource.title or gs_resource.store.name,
                          abstract=gs_resource.abstract or '',
                          owner=instance.owner)
    else:
        msg = "There isn't a geoserver resource for this layer: %s" % instance.name
        logger.exception(msg)
        raise Exception(msg)

    # Get metadata links
    metadata_links = []
    for link in instance.link_set.metadata():
        metadata_links.append((link.mime, link.name, link.url))

    gs_resource.metadata_links = metadata_links
    # gs_resource should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        try:
            gs_catalog.save(gs_resource)
        except geoserver.catalog.FailedRequestError as e:
            msg = ('Error while trying to save resource named %s in GeoServer, '
                   'try to use: "%s"' % (gs_resource, str(e)))
            e.args = (msg,)
            logger.exception(e)

    # Update Attribution link
    if instance.poc:
        # gsconfig now utilizes an attribution dictionary
        gs_resource.attribution = {'title': str(instance.poc),
                                   'width': None,
                                   'height': None,
                                   'href': None,
                                   'url': None,
                                   'type': None}
        profile = Profile.objects.get(username=instance.poc.username)
        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        gs_resource.attribution_link = site_url + profile.get_absolute_url()
        # gs_resource should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                gs_catalog.save(gs_resource)
            except geoserver.catalog.FailedRequestError as e:
                msg = ('Error while trying to save layer named %s in GeoServer, '
                       'try to use: "%s"' % (gs_resource, str(e)))
                e.args = (msg,)
                logger.exception(e)

    if isinstance(instance, ResourceBase):
        if hasattr(instance, 'layer'):
            instance = instance.layer
        else:
            return

    # Save layer attributes
    set_attributes_from_geoserver(instance)

    # Save layer styles
    set_styles(instance, gs_catalog)

    # set SLD
    sld = instance.default_style.sld_body if instance.default_style else None
    if sld:
        set_layer_style(instance, instance.alternate, sld)

    # Invalidate GeoWebCache for the updated resource
    try:
        _stylefilterparams_geowebcache_layer(instance.alternate)
        _invalidate_geowebcache_layer(instance.alternate)
    except BaseException:
        pass

    if instance.storeType == "remoteStore":
        # Save layer attributes
        set_attributes_from_geoserver(instance)
        return

    """Get information from geoserver.

       The attributes retrieved include:

       * Bounding Box
       * SRID
       * Download links (WMS, WCS or WFS and KML)
       * Styles (SLD)
    """
    # instance.name = instance.name or gs_resource.name
    # instance.title = instance.title or gs_resource.title
    instance.abstract = gs_resource.abstract or ''
    instance.workspace = gs_resource.store.workspace.name
    instance.store = gs_resource.store.name

    try:
        logger.debug(" -------------------------------------------------- ")
        bbox = gs_resource.native_bbox
        logger.debug(bbox)
        logger.debug(" -------------------------------------------------- ")
        # Set bounding box values
        instance.bbox_x0 = bbox[0]
        instance.bbox_x1 = bbox[1]
        instance.bbox_y0 = bbox[2]
        instance.bbox_y1 = bbox[3]
        instance.srid = bbox[4]
    except BaseException:
        pass

    if instance.srid:
        instance.srid_url = "http://www.spatialreference.org/ref/" + \
            instance.srid.replace(':', '/').lower() + "/"
    elif instance.bbox_x0 and instance.bbox_x1 and instance.bbox_y0 and instance.bbox_y1:
        # Guessing 'EPSG:4326' by default
        instance.srid = 'EPSG:4326'
    else:
        raise GeoNodeException("Invalid Projection. Layer is missing CRS!")

    # Iterate over values from geoserver.
    for key in ['alternate', 'store', 'storeType']:
        # attr_name = key if 'typename' not in key else 'alternate'
        # print attr_name
        setattr(instance, key, values[key])

    if settings.RESOURCE_PUBLISHING:
        if instance.is_published != gs_resource.advertised:
            if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
                gs_resource.advertised = 'true'
                gs_catalog.save(gs_resource)

    if not settings.FREETEXT_KEYWORDS_READONLY:
        try:
            if len(instance.keyword_list()) == 0 and gs_resource.keywords:
                for keyword in gs_resource.keywords:
                    if keyword not in instance.keyword_list():
                        instance.keywords.add(keyword)
        except BaseException:
            pass

    if any(instance.keyword_list()):
        keywords = instance.keyword_list()
        gs_resource.keywords = [kw for kw in list(set(keywords))]

        # gs_resource should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                gs_catalog.save(gs_resource)
            except geoserver.catalog.FailedRequestError as e:
                msg = ('Error while trying to save resource named %s in GeoServer, '
                       'try to use: "%s"' % (gs_resource, str(e)))
                e.args = (msg,)
                logger.exception(e)

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

    # Update ResourceBase
    resources = ResourceBase.objects.filter(id=instance.resourcebase_ptr.id)
    resources.update(**to_update)

    # to_update['name'] = instance.name,
    to_update['workspace'] = instance.workspace
    to_update['store'] = instance.store
    to_update['storeType'] = instance.storeType
    to_update['typename'] = instance.alternate

    # Save all the modified information in the instance without triggering signals.
    Layer.objects.filter(id=instance.id).update(**to_update)

    # Refresh from DB
    instance.refresh_from_db()

    # store the resource to avoid another geoserver call in the post_save
    instance.gs_resource = gs_resource

    # Refresh and create the instance default links
    layer = Layer.objects.get(id=instance.id)
    set_resource_default_links(instance, layer, prune=True)

    # some thumbnail generators will update thumbnail_url.  If so, don't
    # immediately re-generate the thumbnail here.  use layer#save(update_fields=['thumbnail_url'])
    if 'update_fields' in kwargs and kwargs['update_fields'] is not None and \
            'thumbnail_url' in kwargs['update_fields']:
        logger.info("... Creating Thumbnail for Layer [%s]" % (instance.alternate))
        create_gs_thumbnail(instance, overwrite=True)

    # NOTTODO by simod: we should not do this!
    # need to be removed when fixing #2015
    catalogue_post_save(instance, Layer)

    # Updating HAYSTACK Indexes if needed
    if settings.HAYSTACK_SEARCH:
        from django.core.management import call_command
        call_command('update_index')


def geoserver_pre_save_maplayer(instance, sender, **kwargs):
    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get('raw', False):
        return

    try:
        instance.local = isinstance(
            gs_catalog.get_layer(
                instance.name),
            GsLayer)
    except EnvironmentError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = 'Could not connect to catalog to verify if layer %s was local' % instance.name
            logger.warn(msg)
        else:
            raise e


def geoserver_post_save_map(instance, sender, **kwargs):
    instance.set_missing_info()
    logger.info("... Creating Thumbnail for Map [%s]" % (instance.title))
    create_gs_thumbnail(instance, overwrite=False, check_bbox=True)
