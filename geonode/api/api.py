from django.contrib.auth.models import User

from geonode.base.models import TopicCategory
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

from taggit.models import Tag

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS


FILTER_TYPES = {
    'layer': Layer,
    'map': Map,
    'document': Document
}

class TypeFilteredResource(ModelResource):
    """ Common resource used to apply faceting to categories and keywords 
    based on the type passed as query parameter in the form type:layer/map/document"""
    count = fields.IntegerField()

    type_filter = None

    def dehydrate_count(self, bundle):
        raise Exception('dehydrate_count not implemented in the child class')

    def build_filters(self, filters={}):

        orm_filters = super(TypeFilteredResource, self).build_filters(filters)

        if 'type' in filters and filters['type'] in FILTER_TYPES.keys():
            self.type_filter = FILTER_TYPES[filters['type']]
        else:
            self.type_filter = None
        return orm_filters


class TagResource(TypeFilteredResource):
    """Tags api"""

    def dehydrate_count(self, bundle):
        count = 0
        if self.type_filter:
            for tagged in bundle.obj.taggit_taggeditem_items.all():
                if tagged.content_type.model_class() == self.type_filter:
                    count += 1
        else:
             count = bundle.obj.taggit_taggeditem_items.count()

        return count

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'keywords'
        allowed_methods = ['get',]
        filtering = {
            'slug': ALL,
        }


class TopicCategoryResource(TypeFilteredResource):
    """Category api"""

    def dehydrate_count(self, bundle):
        count = 0
        if self.type_filter:
            count = bundle.obj.resourcebase_set.instance_of(self.type_filter).count() 
        else:
            count = bundle.obj.resourcebase_set.count()
        return count

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get',]
        filtering = {
            'identifier': ALL,
        }
        

class UserResource(ModelResource):
    """User api"""

    class Meta:
        queryset = User.objects.all()
        resource_name = 'users'
        allowed_methods = ['get',]
        excludes = ['is_staff', 'password', 'is_superuser',
             'is_active', 'date_joined', 'last_login']

        filtering = {
            'username': ALL,
        }



