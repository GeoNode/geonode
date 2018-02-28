from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings

from geonode.maps.models import Map

from CommonField import CommonField


class MapLoad(CommonField):
    map = models.ForeignKey(Map, related_name="map_load")

    def __str__(self):
        return self.map.title
