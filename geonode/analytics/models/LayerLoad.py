from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings

from geonode.layers.models import Layer, UploadSession

from CommonField import CommonField


class LayerLoad(CommonField):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    layer = models.ForeignKey(Layer, null=False, blank=False)

    def __str__(self):
        return self.user.username
