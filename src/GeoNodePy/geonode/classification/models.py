from django.db import models

class TimeStampedModel(models.Model):
    """ 
    An abstract base class model that provides self-updating "created" and "modified" fields. 
    """ 
    created = models.DateTimeField(auto_now_add=True) 
    modified = models.DateTimeField(auto_now=True) 
 
    class Meta: 
        abstract = True


class ClassificationMethod(TimeStampedModel):
    """Used for the GeoConnect style classification tools 
    """
    display_name = models.CharField(max_length=255)
    value_name = models.CharField(max_length=100, unique=True, help_text='Parameter value in the the geoserver api calls')
    is_string_usable = models.BooleanField(default=False)

    sort_order = models.IntegerField(default=10, help_text='display order for user')
    active = models.BooleanField(default=True)


    def __unicode__(self):
        return  '%s (%s)' % (self.display_name, self.value_name)

    class Meta:
        ordering = ('sort_order', 'display_name')


class ColorRamp(TimeStampedModel):
    """Used for the GeoConnect style classification tools 
    """
    display_name = models.CharField(max_length=255, unique=True)
    value_name = models.CharField(max_length=100, help_text='Parameter value in the the geoserver api calls')
    sort_order = models.IntegerField(default=10, help_text='display order for user')
    start_color = models.CharField(max_length=30, blank=True, help_text='hex color with "#", as in "#ffcc00"')
    end_color = models.CharField(max_length=30, blank=True, help_text='hex color with "#", as in "#ffcc00"')
    active = models.BooleanField(default=True)
    
    def __unicode__(self):
        return  '%s (%s)' % (self.display_name, self.value_name)

    class Meta:
        ordering = ('sort_order', 'display_name')
