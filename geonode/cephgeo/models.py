from django.db import models
from geonode.layers.models import Layer
# Create your models here.

class CephDataObject(models.Model)
    name = models.CharField(max_length=40)
    data_type = models.CharField(max_length=10)
    file_ext = models.CharField(max_length=10)
    grid_ref = models.CharField(max_length=10)
    
    def __unicode__(self):
        return "{0}.{1}".format(obj_name, obj_type)

class LayerToCephObjectMap(models.Model)
    shapefile     = models.ForeignKey(Layer)
    ceph_data_obj = models.ForeignKey(CephDataObject)
    
    def __unicode__(self):
        return "{0} -> {1}".format(shapefile, ceph_data_obj)
