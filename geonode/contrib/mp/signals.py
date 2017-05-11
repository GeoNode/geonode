from geonode.layers.models import Layer
from geonode.base.models import Link
from django.conf import settings
import uuid

from djmp.settings import TILESET_CACHE_URL
from .models import Tileset


def tileset_post_save(instance, sender, **kwargs):
    if instance.layer_uuid:  # layer already exists
        layer = Layer.objects.get(uuid=instance.layer_uuid)
    else:
        layer_uuid = str(uuid.uuid1())
        Tileset.objects.filter(pk=instance.pk).update(layer_uuid=layer_uuid)
        layer = Layer.objects.create(
            name=instance.name,
            title=instance.name,
            bbox_x0=instance.bbox_x0,
            bbox_x1=instance.bbox_x1,
            bbox_y0=instance.bbox_y0,
            bbox_y1=instance.bbox_y1,
            uuid=layer_uuid)

    if settings.USE_DISK_CACHE:
        tile_url = '%s%s/%s/{z}/{x}/{y}.png' % (settings.SITEURL, TILESET_CACHE_URL, instance.id)
    else:
        tile_url = "%sdjmp/%d/map/tiles/%s/EPSG3857/{z}/{x}/{y}.png" % (settings.SITEURL, instance.id, instance.name)

    l, __ = Link.objects.get_or_create(
        resource=layer.resourcebase_ptr,
        extension='tiles',
        name="Tiles",
        mime='image/png',
        link_type='image'
    )
    l.url = tile_url
    l.save()


def layer_post_save(instance, sender, **kwargs):
    if not Tileset.objects.filter(layer_uuid=instance.uuid).exists():
        tileset = Tileset.objects.create(
            name=instance.title,
            created_by=instance.owner.username,
            layer_name=instance.typename,
            bbox_x0=instance.bbox_x0,
            bbox_x1=instance.bbox_x1,
            bbox_y0=instance.bbox_y0,
            bbox_y1=instance.bbox_y1,
            source_type='wms',
            server_url=settings.OGC_SERVER['default']['LOCATION'] + 'wms',
            server_username=settings.OGC_SERVER['default']['USER'],
            server_password=settings.OGC_SERVER['default']['PASSWORD'],
            cache_type='file',
            directory_layout='tms',
            layer_zoom_stop=settings.CACHE_ZOOM_STOP,
            layer_zoom_start=settings.CACHE_ZOOM_START,
            layer_uuid=instance.uuid
            )

        if settings.CACHE_ON_LAYER_LOAD:
            tileset.seed()


def layer_post_delete(instance, sender, **kwargs):
    if Tileset.objects.filter(layer_uuid=instance.uuid).exists():
        Tileset.objects.filter(layer_uuid=instance.uuid).delete()
