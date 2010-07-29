from django.db import models
from geonode.maps.models import Layer
from django.utils.translation import ugettext as _

class Hazard(models.Model): 
    name = models.CharField(_('name'), max_length=128)

    def __str__(self): 
        return "%s Hazard" % self.name

class Period(models.Model):
    hazard = models.ForeignKey(Hazard, verbose_name=_('hazard'))
    layer = models.OneToOneField(Layer, verbose_name=('layer'))
    length = models.IntegerField(_('length'))
