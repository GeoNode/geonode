from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from geonode.maps.models import Map
from geonode.layers.models import Layer

from CommonField import CommonField


class PinpointUserActivity(CommonField):
    ACTIVITY_CHOICES = (
        ('pan', _('Pan')),
        ('zoom', _('Zoom')),
        ('click', _('Click')),
    )

    layer = models.ForeignKey(Layer, null=True, blank=True, on_delete=models.CASCADE)
    map = models.ForeignKey(Map, null=True, blank=True, on_delete=models.CASCADE)
    activity_type = models.CharField(_('Activity Type'),
                                     choices=ACTIVITY_CHOICES,
                                     max_length=10,
                                     help_text='Activity Type')
    # convert latitude and longitude into WGS84 (SRID 4326) before save
    # store geom
    the_geom = models.GeometryField(_('Geometry'), blank=True, null=True, help_text='Geometry')

    def __str__(self):
        return self.user.username
