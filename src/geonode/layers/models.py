from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Layer(models.Model):
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200) 
    abstract = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    created_on = models.DateField()
    last_edited = models.DateField()
    namespace = models.CharField(max_length=200)
    owner = models.ForeignKey(User, related_name='owned_layers')    

    def __unicode__(self):
        return "%s:%s" %(self.namespace, self.name)

    #@@has to be a better way to do this?
    def get_absolute_url(self):
        return '/layers/%i' % self.id
