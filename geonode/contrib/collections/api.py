import json

from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS, ALL

from geonode.api.api import ProfileResource, GroupResource
from geonode.api.resourcebase_api import ResourceBaseResource

from .models import Collection


class CollectionResource(ModelResource):

    users = fields.ToManyField(ProfileResource, attribute=lambda bundle: bundle.obj.group.group.user_set.all(), full=True)
    group = fields.ToOneField(GroupResource, 'group', full=True)
    resources = fields.ToManyField(ResourceBaseResource, 'resources', full=True)


    class Meta:
        queryset = Collection.objects.order_by('-group')
        ordering = ['group']
        allowed_methods = ['get']
        resource_name = 'collections'
        filtering = {
            'group': ALL_WITH_RELATIONS,
            'id': ALL
        }
