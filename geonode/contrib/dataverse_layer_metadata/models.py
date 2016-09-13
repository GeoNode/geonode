from django.db import models
from geonode.maps.models import Layer
from shared_dataverse_information.dataverse_info.models import DataverseInfo

class DataverseLayerMetadata(DataverseInfo):
    """
    If a map layer is created using a dataverse file, 
    this objects contains Dataverse specific info on the file.
    
    In addition to supplying metadata, it can also be used to identify 
    which Layers were created using Dataverse files.
    """
    map_layer = models.ForeignKey(Layer, on_delete=models.CASCADE)      # if the Layer is deleted, remove this DataverseMetadata object
    
    
    def __unicode__(self):
        return '%s (%s -> %s)' % (self.datafile_label, self.dataverse_name, self.dataset_name)
        
    class Meta:
        ordering = ('-modified',  )
        verbose_name_plural = 'Dataverse Metadata'
    