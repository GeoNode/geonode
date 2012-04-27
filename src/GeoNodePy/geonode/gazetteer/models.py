# -*- coding: UTF-8 -*-
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import ugettext as _
import logging
from geonode.maps.models import Layer, LayerAttribute

logger = logging.getLogger("geonode.maps.gazetteer.models")

#class PlaceName(models.Model):
#    layer = models.ForeignKey(Layer, blank=False, null=False)
#    layer_attribute = models.ForeignKey(LayerAttribute, blank=False, null=False)
#    feature = models.GeometryField()
#    feature_type = models.CharField(_('Attribute Type'), max_length=50)
#    feature_fid = models.BigIntegerField()
#    latitude = models.FloatField()
#    longitude = models.FloatField()
#    place_name = models.CharField(max_length=2048)
#    start_date = models.DateField()
#    end_date = models.DateField()
#    project = models.CharField(max_length=256)
#    objects = models.GeoManager()




