import json
import time

from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Count

from avatar.templatetags.avatar_tags import avatar_url
from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ResourceBase
from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile

from taggit.models import Tag
from django.core.serializers.json import DjangoJSONEncoder
from tastypie.serializers import Serializer
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL
from tastypie.utils import trailing_slash


FILTER_TYPES = {
    'layer': Layer,
    'map': Map,
    'document': Document
}


class CountJSONSerializer(Serializer):
    """Custom serializer to post process the api and add counts"""

    def get_resources_counts(self, options):
        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.objects.all()
        else:
            resources = get_objects_for_user(
                options['user'],
                'base.view_resourcebase'
            )
        if settings.RESOURCE_PUBLISHING:
            resources = resources.filter(is_published=True)

        if options['title_filter']:
            resources = resources.filter(title__icontains=options['title_filter'])

        if options['type_filter']:
            resources = resources.instance_of(options['type_filter'])

        counts = resources.values(options['count_type']).annotate(count=Count(options['count_type']))

        return dict([(c[options['count_type']], c['count']) for c in counts])

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        counts = self.get_resources_counts(options)
        for item in data['objects']:
            item['count'] = counts.get(item['id'], 0)
        # Add in the current time.
        data['requested_time'] = time.time()

        return json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True)


class TypeFilteredResource(ModelResource):
    """ Common resource used to apply faceting to categories, keywords, and
    regions based on the type passed as query parameter in the form
    type:layer/map/document"""

    count = fields.IntegerField()

    type_filter = None
    title_filter = None

    def build_filters(self, filters={}):

        orm_filters = super(TypeFilteredResource, self).build_filters(filters)

        if 'type' in filters and filters['type'] in FILTER_TYPES.keys():
            self.type_filter = FILTER_TYPES[filters['type']]
        else:
            self.type_filter = None
        if 'title__icontains' in filters:
            self.title_filter = filters['title__icontains']

        return orm_filters


class TagResource(TypeFilteredResource):
    """Tags api"""

    def serialize(self, request, data, format, options={}):
        options['title_filter'] = self.title_filter
        options['type_filter'] = self.type_filter
        options['count_type'] = 'keywords'
        options['user'] = request.user

        return super(TagResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = Tag.objects.all().order_by('name')
        resource_name = 'keywords'
        allowed_methods = ['get']
        filtering = {
            'slug': ALL,
        }
        serializer = CountJSONSerializer()


class RegionResource(TypeFilteredResource):
    """Regions api"""

    def serialize(self, request, data, format, options={}):
        options['title_filter'] = self.title_filter
        options['type_filter'] = self.type_filter
        options['count_type'] = 'regions'
        options['user'] = request.user

        return super(RegionResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = Region.objects.all().order_by('name')
        resource_name = 'regions'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
        }
        # To activate the counts on regions uncomment the following line
        # serializer = CountJSONSerializer()


class TopicCategoryResource(TypeFilteredResource):
    """Category api"""

    def serialize(self, request, data, format, options={}):
        options['title_filter'] = self.title_filter
        options['type_filter'] = self.type_filter
        options['count_type'] = 'category'
        options['user'] = request.user

        return super(TopicCategoryResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get']
        filtering = {
            'identifier': ALL,
        }
        serializer = CountJSONSerializer()


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
        return reverse('group_detail', args=[bundle.obj.slug])

    class Meta:
        queryset = GroupProfile.objects.all()
        resource_name = 'groups'
        allowed_methods = ['get']
        filtering = {
            'name': ALL
        }
        ordering = ['title', 'last_modified']


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

        semi_filtered = super(
            ProfileResource,
            self).apply_filters(
            request,
            applicable_filters)

        if group is not None:
            semi_filtered = semi_filtered.filter(
                groupmember__group__slug=group)

        return semi_filtered

    def dehydrate_email(self, bundle):
        email = ''
        if bundle.request.user.is_authenticated():
            email = bundle.obj.email
        return email

    def dehydrate_layers_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').instance_of(Layer)
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_maps_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').instance_of(Map)
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_documents_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').instance_of(Document)
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_avatar_100(self, bundle):
        return avatar_url(bundle.obj, 100)

    def dehydrate_profile_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_current_user(self, bundle):
        return bundle.request.user.username == bundle.obj.username

    def dehydrate_activity_stream_url(self, bundle):
        return reverse(
            'actstream_actor',
            kwargs={
                'content_type_id': ContentType.objects.get_for_model(
                    bundle.obj).pk,
                'object_id': bundle.obj.pk})

    def prepend_urls(self):
        if settings.HAYSTACK_SEARCH:
            return [
                url(r"^(?P<resource_name>%s)/search%s$" % (
                    self._meta.resource_name, trailing_slash()
                ),
                    self.wrap_view('get_search'), name="api_get_search"),
            ]
        else:
            return []

    class Meta:
        queryset = get_user_model().objects.exclude(username='AnonymousUser')
        resource_name = 'profiles'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
        }
