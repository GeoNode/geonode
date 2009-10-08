from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Map(models.Model):
    # metadata fields
    title = models.CharField(max_length=200)
    abstract = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    featured = models.BooleanField()
    endorsed = models.BooleanField()
    owner = models.ForeignKey(User, related_name='owned_maps')    
    contributors = models.ManyToManyField(User, related_name='maps_contributed_to')

    # viewer configuration
    zoom = models.IntegerField()
    center_lat = models.FloatField()
    center_lon = models.FloatField()

    def __unicode__(self):
        return '%s by %s' % (self.title, self.contact)

    #@@has to be a better way to do this?
    def get_absolute_url(self):
        return '/maps/%i' % self.id


class MapLayer(models.Model):
    name = models.CharField(max_length=200)
    ows_url = models.URLField()
    group = models.CharField(max_length=200,blank=True)
    stack_order = models.IntegerField()
    map = models.ForeignKey(Map)

    class Meta:
        ordering = ["stack_order"]

    def __unicode__(self):
        return '%s?layers=%s' % (self.ows_url, self.name)


