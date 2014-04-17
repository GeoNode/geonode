from django.contrib.auth.models import User

from geonode.base.models import TopicCategory

from taggit.models import Tag

from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS


class TagResource(ModelResource):
    """Tags api"""

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'keywords'
        allowed_methods = ['get',]
        filtering = {
            'slug': ALL,
        }


class TopicCategoryResource(ModelResource):
    """Category api"""

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



