from django.contrib.gis.db import models
from django.db.models.fields import Field
from django.utils.translation import ugettext as _
from datautil.date import FlexiDate

#Querying postgis database for features then saving as django model object is significantly slower than
#doing everything via SQL on postgis database only.


class GazetteerEntry(models.Model):
    layer_name = models.CharField(_('Layer Name'), max_length=255, blank=False, null=False)
    layer_attribute = models.CharField(_('Layer Attribute'), max_length=255, blank=False, null=False)
    feature_type = models.CharField(_('Feature Type'), max_length=255, blank=False, null=False)
    feature_fid = models.BigIntegerField(_('Feature FID'), blank=False, null=False)
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    place_name = models.TextField(_('Place name'))
    start_date = models.DateTimeField(_('Start Date'), blank=True, null=True)
    end_date = models.DateTimeField(_('End Date'), blank=True, null=True)
    project = models.CharField(_('Project'), max_length=255,  blank=True, null=True)
    feature = models.GeometryField(_('Geometry'), null=True, blank=True)
    objects = models.GeoManager()

    class Meta:
        unique_together = (("layer_name", "layer_attribute", "feature_fid"))

