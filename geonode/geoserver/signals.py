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
from requests.exceptions import ConnectionError

from deprecated import deprecated
from geoserver.layer import Layer as GsLayer

from django.db.models import Q
from django.dispatch import Signal

# use different name to avoid module clash
from geonode.utils import is_monochromatic_image
from geonode.decorators import on_ogc_backend
from geonode.geoserver.helpers import gs_catalog, ogc_server_settings
from geonode.geoserver.tasks import geoserver_create_thumbnail
from geonode.layers.models import Dataset
from geonode.services.enumerations import CASCADED

from . import BACKEND_PACKAGE
from .tasks import geoserver_cascading_delete, geoserver_post_save_datasets

logger = logging.getLogger("geonode.geoserver.signals")

geoserver_automatic_default_style_set = Signal()

geofence_rule_assign = Signal()


def geoserver_delete(typename):
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        geoserver_cascading_delete.apply_async(args=(typename,), expiration=30)


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_pre_delete(instance, sender, **kwargs):
    """Removes the layer from GeoServer"""
    # cascading_delete should only be called if
    # ogc_server_settings.BACKEND_WRITE_ENABLED == True
    if getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
        if (
            not hasattr(instance, "remote_service")
            or instance.remote_service is None
            or instance.remote_service.method == CASCADED
        ):
            if instance.alternate:
                geoserver_cascading_delete.apply_async(args=(instance.alternate,), expiration=30)


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
    geoserver_post_save_datasets.apply_async(args=(instance.id, args, kwargs), expiration=30)


@on_ogc_backend(BACKEND_PACKAGE)
def geoserver_pre_save_maplayer(instance, sender, **kwargs):
    # If this object was saved via fixtures,
    # do not do post processing.
    if kwargs.get("raw", False):
        return

    try:
        instance.local = isinstance(gs_catalog.get_layer(instance.name), GsLayer)
    except ConnectionError as e:
        logger.warning(f"Could not connect to catalog to verify if layer {instance.name} was local: {e}")
    except OSError as e:
        logger.warning(f"***** OSERROR TYPE:{type(e)} ERR:{e} ERRNO:{e.errno}")
        if e.errno == errno.ECONNREFUSED:
            msg = f"Could not connect to catalog to verify if layer {instance.name} was local"
            logger.warning(msg)
        else:
            raise e

    # Set dataset
    if instance.dataset is None:
        dataset_queryset = Dataset.objects.filter(Q(alternate=instance.name) | Q(name=instance.name))
        if instance.local and instance.store:
            dataset_queryset = dataset_queryset.filter(store=instance.store)
        elif instance.ows_url:
            dataset_queryset = dataset_queryset.filter(remote_service__base_url=instance.ows_url)
        try:
            instance.dataset = dataset_queryset.get()
        except (Dataset.DoesNotExist, Dataset.MultipleObjectsReturned):
            pass


@deprecated(version="3.2.1", reason="Use direct calls to the ReourceManager.")
def geoserver_post_save_map(instance, sender, created, **kwargs):
    instance.set_missing_info()
    if not created:
        if not instance.thumbnail_url:
            logger.debug(f"... Creating Thumbnail for Map [{instance.title}]")
            geoserver_create_thumbnail.apply_async(
                args=(
                    instance.id,
                    False,
                    True,
                ),
                expiration=30,
            )


@deprecated(version="3.2.1", reason="Use direct calls to the ReourceManager.")
def geoserver_set_thumbnail(instance, **kwargs):
    # Creating Dataset Thumbnail
    # some thumbnail generators will update thumbnail_url.  If so, don't
    # immediately re-generate the thumbnail here.  use layer#save(update_fields=['thumbnail_url'])
    try:
        logger.debug(f"... Creating Thumbnail for Dataset {instance.title}")
        _recreate_thumbnail = False
        if (
            "update_fields" in kwargs
            and kwargs["update_fields"] is not None
            and "thumbnail_url" in kwargs["update_fields"]
        ):
            _recreate_thumbnail = True
        if not instance.thumbnail_url or is_monochromatic_image(instance.thumbnail_url):
            _recreate_thumbnail = True
        if _recreate_thumbnail:
            geoserver_create_thumbnail.apply_async(
                args=(
                    instance.id,
                    False,
                    True,
                ),
                expiration=30,
            )
        else:
            logger.debug(f"... Thumbnail for Dataset {instance.title} already exists: {instance.thumbnail_url}")
    except Exception as e:
        logger.exception(e)
