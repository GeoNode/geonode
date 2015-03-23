from django.db import models
from geonode.layers.models import Layer
import json

class CephDataObject(models.Model):
    size_in_bytes   = models.IntegerField()
    file_hash       = models.CharField(max_length=30)
    name            = models.CharField(max_length=100)
    last_modified   = models.DateTimeField()
    content_type    = models.CharField(max_length=20)
    geo_type        = models.CharField(max_length=20)
    grid_ref        = models.CharField(max_length=10)
    
    def __unicode__(self):
        return "{0}:{1}".format(self.name, self.geo_type)

class LayerToCephObjectMap(models.Model):
    shapefile     = models.ForeignKey(Layer)
    ceph_data_obj = models.ForeignKey(CephDataObject)
    
    def __unicode__(self):
        return "{0} -> {1}".format(self.shapefile, self.ceph_data_obj)

