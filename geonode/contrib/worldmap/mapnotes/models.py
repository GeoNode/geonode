from django.contrib.gis.db import models
from geonode.people.models import Profile
from geonode.maps.models import Map
from django.utils.translation import ugettext_lazy as _


class MapNote(models.Model):
    geometry = models.GeometryField(srid=4326, null=True, blank=True)
    owner = models.ForeignKey(Profile)
    map = models.ForeignKey(Map)
    created_dttm = models.DateTimeField(auto_now_add=True)
    modified_dttm = models.DateTimeField(auto_now=True)
    content = models.TextField(_('Content'), blank=True, null=True)
    title = models.CharField(_('Title'), max_length=255, blank=True, null=True)

    def owner_id(self):
        return self.owner.id

    objects = models.GeoManager()
