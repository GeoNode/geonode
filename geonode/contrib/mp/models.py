from django.db import models
from django.db.models import signals
from django.conf import settings

from djmp.models import Tileset
from geonode.layers.models import Layer
from geonode.base.models import Link

from .signals import tileset_post_save, layer_post_save


signals.post_save.connect(tileset_post_save, sender=Tileset)

if settings.USE_DJMP_FOR_GEONODE_LAYERS:
    signals.post_save.connect(layer_post_save, sender=Layer)
