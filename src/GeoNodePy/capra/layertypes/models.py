from django.db import models
import geonode.maps.models as maps
from django.utils.translation import ugettext_lazy as _

class LayerTypeManager(models.Manager):
    def type_for_layer(self, layer):
        try: 
            link = LayerTypeAssociation.objects.get(layer=layer)
            return link.type
        except LayerTypeAssociation.DoesNotExist:
            return None

class LayerType(models.Model):
    """A layer category, such as 'hazard' or 'base'."""
    name = models.CharField('name', max_length=50, unique=True, db_index=True)
    objects = LayerTypeManager()

    def __unicode__(self): 
        return self.name

class LayerTypeAssociationManager(models.Manager):
    def layers_for_type(self, type):
        """Get all of the layers for a given type"""
        pass

    def layers_by_type(self):
        """Get a listing of all layers grouped by type"""
        pass

class LayerTypeAssociation(models.Model):
    """The link between a layer type and the actual layer."""
    objects = LayerTypeAssociationManager()

    category = models.ForeignKey(LayerType)
    layer = models.ForeignKey(maps.Layer)

    class Meta:
        verbose_name = _('Data Category')
        verbose_name_plural = _('Data Categories')

    def __unicode__(self):
        return "%s [%s]" % (self.layer, self.category)
