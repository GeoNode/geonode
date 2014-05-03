from django.contrib.auth.models import User
from django.db.models import Count

from geonode.base.models import TopicCategory

from taggit.models import Tag

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS


class TagResource(ModelResource):
    """Tags api"""

    count = fields.IntegerField()

    class Meta:
        queryset = Tag.objects.annotate(Count('resourcebase'))
        resource_name = 'keywords'
        allowed_methods = ['get',]
        filtering = {
            'slug': ALL,
        }

    def dehydrate_count(self, bundle):
        return bundle.obj.resourcebase__count


class TopicCategoryResource(ModelResource):
    """Category api"""

    count = fields.IntegerField()

    class Meta:
        queryset = TopicCategory.objects.annotate(Count('resourcebase'))
        resource_name = 'categories'
        allowed_methods = ['get',]
        filtering = {
            'identifier': ALL,
        }

    def dehydrate_count(self, bundle):
        return bundle.obj.resourcebase__count
        

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



