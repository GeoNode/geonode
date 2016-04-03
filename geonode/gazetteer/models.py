from django.utils.translation import ugettext as _
from django.contrib.gis.db import models

# Querying postgis database for features then saving as django model object is
# significantly slower than doing everything via SQL on postgis database only.
from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^django\.contrib\.gis\.db\.models\.fields\.GeometryField"])


class GazetteerEntry(models.Model):
    layer_name = models.CharField(_('Layer Name'), max_length=255, blank=False, null=False)
    layer_attribute = models.CharField(_('Layer Attribute'), max_length=255, blank=False, null=False)
    feature_type = models.CharField(_('Feature Type'), max_length=255, blank=False, null=False)
    feature_fid = models.BigIntegerField(_('Feature FID'), blank=False, null=False)
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    place_name = models.TextField(_('Place name'))
    start_date = models.TextField(_('Start Date'), blank=True, null=True)
    end_date = models.TextField(_('End Date'), blank=True, null=True)
    julian_start = models.IntegerField(_('Julian Date Start'), blank=True, null=True)
    julian_end = models.IntegerField(_('Julian Date End'), blank=True, null=True)
    project = models.CharField(_('Project'), max_length=255,  blank=True, null=True)
    feature = models.GeometryField(_('Geometry'), null=True, blank=True)
    username = models.CharField(_('User Name'), max_length=30, blank=True, null=True)
    objects = models.GeoManager()

    class Meta:
        unique_together = (("layer_name", "layer_attribute", "feature_fid"))

