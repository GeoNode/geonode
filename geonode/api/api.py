from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from avatar.templatetags.avatar_tags import avatar_url

from geonode.base.models import TopicCategory
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile
from geonode.groups.models import Group

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
                if tagged.content_object and tagged.content_type.model_class() == self.type_filter and \
                    bundle.request.user.has_perm('view_resourcebase', tagged.content_object):
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
        resources = bundle.obj.resourcebase_set.instance_of(self.type_filter).get_real_instances() if \
            self.type_filter else bundle.obj.resourcebase_set.get_real_instances()

        for resource in resources:
            if bundle.request.user.has_perm('view_resourcebase', resource):
                count += 1

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
        queryset = get_user_model().objects.all()
        resource_name = 'users'
        allowed_methods = ['get',]
        excludes = ['is_staff', 'password', 'is_superuser',
             'is_active', 'date_joined', 'last_login']

        filtering = {
            'username': ALL,
        }


class GroupResource(ModelResource):
    """Groups api"""

    detail_url = fields.CharField()
    member_count = fields.IntegerField()
    manager_count = fields.IntegerField()

    def dehydrate_member_count(self, bundle):
        return bundle.obj.member_queryset().count()

    def dehydrate_manager_count(self, bundle):
        return bundle.obj.get_managers().count()

    def dehydrate_detail_url(self, bundle):
        return reverse('group_detail',  args=[bundle.obj.slug,]) 

    class Meta:
        queryset = Group.objects.all()
        resource_name = 'groups'
        allowed_methods = ['get',]
        filtering = {
            'name': ALL
        }
        ordering = ['title', 'last_modified',]


class ProfileResource(ModelResource):
    """Profile api"""
    avatar_100 = fields.CharField(null=True)
    profile_detail_url = fields.CharField()
    email = fields.CharField(default='')
    layers_count = fields.IntegerField(default=0)
    maps_count = fields.IntegerField(default=0)
    documents_count = fields.IntegerField(default=0)
    current_user = fields.BooleanField(default=False)
    activity_stream_url = fields.CharField(null=True)

    def build_filters(self, filters={}):
        """adds filtering by group functionality"""

        orm_filters = super(ProfileResource, self).build_filters(filters)
        
        if 'group' in filters:
            orm_filters['group'] = filters['group']

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """filter by group if applicable by group functionality"""

        group = applicable_filters.pop('group', None)

        semi_filtered = super(ProfileResource, self).apply_filters(request, applicable_filters)

        if group is not None:
            semi_filtered = semi_filtered.filter(user__groupmember__group__slug=group)
            
        return semi_filtered

    def dehydrate_email(self, bundle):
        email = ''
        if bundle.request.user.is_authenticated():
            email = bundle.obj.email
        return email

    def dehydrate_layers_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Layer).count()

    def dehydrate_maps_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Map).count()

    def dehydrate_documents_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Document).count()

    def dehydrate_avatar_100(self, bundle):
        return avatar_url(bundle.obj, 100)

    def dehydrate_profile_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_current_user(self, bundle):
        return bundle.request.user.username == bundle.obj.username

    def dehydrate_activity_stream_url(self, bundle):
        return reverse('actstream_actor', kwargs={
            'content_type_id': ContentType.objects.get_for_model(bundle.obj).pk, 
            'object_id': bundle.obj.pk})

    class Meta:
        queryset = get_user_model().objects.exclude(username='AnonymousUser')
        resource_name = 'profiles'
        allowed_methods = ['get',]
        ordering = ['name']
        