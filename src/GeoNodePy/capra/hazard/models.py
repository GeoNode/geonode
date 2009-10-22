from django.db import models

# Create your models here.

class Hazard(models.Model): 
    name = models.CharField(max_length=128)

    def __str__(self): 
        return "%s Hazard" % self.name

class Period(models.Model):
    hazard = models.ForeignKey(Hazard)
    typename = models.CharField(max_length=128)
    length = models.IntegerField()
