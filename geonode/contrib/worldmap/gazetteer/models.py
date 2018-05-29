from django.utils.translation import ugettext as _
from django.contrib.gis.db import models
from django.db.models import signals

from geonode.layers.models import Layer, Attribute

# Querying postgis database for features then saving as django model object is
# significantly slower than doing everything via SQL on postgis database only.
# from django.modelsinspector import add_introspection_rules

# add_introspection_rules([], ["^django\.contrib\.gis\.db\.models\.fields\.GeometryField"])


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
    project = models.CharField(_('Project'), max_length=255, blank=True, null=True)
    feature = models.GeometryField(_('Geometry'), null=True, blank=True)
    username = models.CharField(_('User Name'), max_length=30, blank=True, null=True)
    objects = models.GeoManager()

    class Meta:
        unique_together = (("layer_name", "layer_attribute", "feature_fid"))


class GazetteerAttribute(models.Model):
    attribute = models.OneToOneField(
        Attribute,
        blank=False,
        null=False)
    in_gazetteer = models.BooleanField(default=False)
    is_start_date = models.BooleanField(default=False)
    is_end_date = models.BooleanField(default=False)
    date_format = models.TextField(blank=True, null=True)

    def layer_name(self):
        return self.attribute.layer.name


def gazetteer_delete_layer(instance, sender, **kwargs):
    GazetteerEntry.objects.filter(layer_name=instance.name).delete()
    print 'Removing gazetteer entries for the layer'


signals.pre_delete.connect(gazetteer_delete_layer, sender=Layer)
