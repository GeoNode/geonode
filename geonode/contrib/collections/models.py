from django.db import models

from geonode.base.models import ResourceBase
from geonode.groups.models import GroupProfile

class Collection(models.Model):
    """
    A collection is a set of resouces linked to a GeoNode group
    """
    group = models.ForeignKey(GroupProfile, related_name='group_collections')
    resources = models.ManyToManyField(ResourceBase, related_name='resource_collections', blank=True, null=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)

    def __unicode__(self):
        return self.name
