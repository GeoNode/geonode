from django.db import models
from geonode.maps.models import Layer

class Hazard(models.Model): 
    name = models.CharField(max_length=128)

    def __str__(self): 
        return "%s Hazard" % self.name

class Period(models.Model):
    hazard = models.ForeignKey(Hazard)
    layer = models.OneToOneField(Layer)
    length = models.IntegerField()
