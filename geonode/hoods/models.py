from django.db import models
from django.db.models import signals
from django.conf import settings
from geonode.maps.models import Map
from geonode.hoods.views import update_hood_map
import logging

# Create your models here.

logger = logging.getLogger("geonode.hoods.models")

def post_save_map(instance, sender, **kwargs):
    if instance.officialurl == 'boston' and settings.HOODS_TEMPLATE_ID is not None:
        logger.info("Update hood map")
        update_hood_map()
    else:
        logger.info("Dont update hood map")

signals.post_save.connect(post_save_map, sender=Map)