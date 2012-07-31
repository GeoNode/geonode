from django.db import models
from geonode.maps.models import Layer

STATUS_VALUES = [
    'pending',
    'failed'
]

class GazetteerUpdateJob(models.Model):
    layer = models.ForeignKey(Layer, blank=False, null=False, unique=True)
    status = models.CharField(choices= [(x, x) for x in STATUS_VALUES], max_length=10, blank=False, null=False, default='pending')
