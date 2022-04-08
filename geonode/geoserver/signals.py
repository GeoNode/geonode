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

from geoserver.layer import Layer as GsLayer

from django.conf import settings
from django.dispatch import receiver, Signal
from django.forms.models import model_to_dict
from django.contrib.staticfiles.templatetags import staticfiles

# use different name to avoid module clash
from geonode.utils import (
    is_monochromatic_image,
    json_serializer_producer)
from geonode.decorators import on_ogc_backend
from geonode.geoserver.helpers import (
    gs_catalog,
    ogc_server_settings)
from geonode.geoserver.tasks import geoserver_create_thumbnail
from geonode.layers.models import Layer
from geonode.services.enumerations import CASCADED

from . import BACKEND_PACKAGE
from .tasks import geoserver_cascading_delete, geoserver_post_save_layers

logger = logging.getLogger("geonode.geoserver.signals")

geoserver_post_save_complete = Signal(providing_args=['instance'])


def geoserver_delete(typename):
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        geoserver_cascading_delete.apply_async((typename,))


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer
    """
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        if instance.remote_service is None or instance.remote_service.method == CASCADED:
            if instance.alternate:
                geoserver_cascading_delete.apply_async((instance.alternate,))


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_pre_save(*args, **kwargs):
    # nothing to do here, processing is pushed to post-save
    pass


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_post_save(instance, sender, created, **kwargs):
    from geonode.messaging import producer
    # this is attached to various models, (ResourceBase, Document)
    # so we should select what will be handled here
    if isinstance(instance, Layer):
        instance_dict = model_to_dict(instance)
        payload = json_serializer_producer(instance_dict)
        try:
            producer.geoserver_upload_layer(payload)
        except Exception as e:
            logger.error(e)
        if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
            instance.set_dirty_state()


@on_ogc_backend(BACKEND_PACKAGE)
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
    geoserver_post_save_layers.apply(
        (instance.id, args, kwargs))


@on_ogc_backend(BACKEND_PACKAGE)
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
    except OSError as e:
        if e.errno == errno.ECONNREFUSED:
            msg = f'Could not connect to catalog to verify if layer {instance.name} was local'
            logger.warn(msg)
        else:
            raise e


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_post_save_map(instance, sender, created, **kwargs):
    instance.set_missing_info()
    if not created:
        if not instance.thumbnail_url or \
                instance.thumbnail_url == staticfiles.static(settings.MISSING_THUMBNAIL):
            logger.debug(f"... Creating Thumbnail for Map [{instance.title}]")
            geoserver_create_thumbnail.apply((instance.id, False, True, ))


@receiver(geoserver_post_save_complete)
def geoserver_post_save_thumbnail(sender, instance, **kwargs):
    # Creating Layer Thumbnail
    # some thumbnail generators will update thumbnail_url.  If so, don't
    # immediately re-generate the thumbnail here.  use layer#save(update_fields=['thumbnail_url'])
    try:
        logger.debug(f"... Creating Thumbnail for Layer {instance.title}")
        _recreate_thumbnail = False
        if 'update_fields' in kwargs and kwargs['update_fields'] is not None and \
                'thumbnail_url' in kwargs['update_fields']:
            _recreate_thumbnail = True
        if not instance.thumbnail_url or \
                instance.thumbnail_url == staticfiles.static(settings.MISSING_THUMBNAIL) or \
                is_monochromatic_image(instance.thumbnail_url):
            _recreate_thumbnail = True
        if _recreate_thumbnail:
            geoserver_create_thumbnail.apply((instance.id, False, True, ))
        else:
            logger.debug(f"... Thumbnail for Layer {instance.title} already exists: {instance.thumbnail_url}")
    except Exception as e:
        logger.exception(e)
