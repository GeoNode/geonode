from django.db import models
from geonode.classification.models import TimeStampedModel
from geonode.maps.models import Layer

class DataverseInfo(models.Model):
    """
    If a map layer is created using a dataverse file, 
    this objects contains Dataverse specific info on the file.
    
    In addition to supplying metadata, it can also be used to identify 
    which Layers were created using Dataverse files.
    """
    map_layer = models.ForeignKey(Layer, on_delete=models.CASCADE)  # if the Layer is deleted, remove this DataverseInfo object
    
    # dv user who created layer
    dv_username = models.CharField(max_length=255, db_index=True)
    dv_user_email = models.EmailField(db_index=True)

    # dataset url
    dataset_url = models.URLField(max_length=255, blank=True)
    
    # dataverse info
    dataverse_name = models.CharField(max_length=255, db_index=True)
    dataverse_description = models.TextField(blank=True) 
    
    # dataset info
    doi = models.CharField('DOI', max_length=255, blank=True)
    dataset_id = models.IntegerField(default=-1)  # for API calls.  
    dataset_version_id = models.CharField(max_length=25)  # for API calls.
    dataset_name = models.CharField(max_length=255, blank=True)  # for display
    dataset_description = models.TextField(blank=True) 

    # datafile info
    datafile_label = models.CharField(max_length=255, help_text='original file name')  
    datafile_description = models.TextField(blank=True)   
        
    # timestamps
    created = models.DateTimeField(auto_now_add=True) 
    modified = models.DateTimeField(auto_now=True)
    
    
    def __unicode__(self):
        return '%s (%s -> %s)' % (self.datafile_label, self.dataverse_name, self.dataset_name)
        
    class Meta:
        ordering = ('-modified',  )
        verbose_name_plural = 'Dataverse Info'
    