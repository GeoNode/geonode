from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Q
from django.utils import formats

from avatar.templatetags.avatar_tags import avatar_url
from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ResourceBase
from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.datarequests.models import DataRequestProfile
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile

from taggit.models import Tag

from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.resources import ModelResource
from tastypie.constants import ALL
from tastypie.utils import trailing_slash

from .authorization import GeoNodeAuthorization, DataRequestAuthorization


FILTER_TYPES = {
    'layer': Layer,
    'map': Map,
    'document': Document,
    'data_request': DataRequestProfile,
}


class TypeFilteredResource(ModelResource):

    """ Common resource used to apply faceting to categories, keywords, and
    regions based on the type passed as query parameter in the form
    type:layer/map/document"""
    count = fields.IntegerField()

    type_filter = None
    title_filter = None

    def dehydrate_count(self, bundle):
        raise Exception('dehydrate_count not implemented in the child class')

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

    def dehydrate_count(self, bundle):
        count = 0
        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.published.all()
        else:
            resources = get_objects_for_user(
                bundle.request.user,
                'base.view_resourcebase'
            )
        if settings.RESOURCE_PUBLISHING:
            resources = resources.filter(is_published=True)

        if self.title_filter:
            resources = resources.filter(title__icontains=self.title_filter)
        resources_ids = resources.values_list('id', flat=True)

        tags = bundle.obj.taggit_taggeditem_items
        if self.type_filter:
            ctype = ContentType.objects.get_for_model(self.type_filter)
            count = tags.filter(
                content_type=ctype).filter(object_id__in=resources_ids).count()
        else:
            count = tags.filter(object_id__in=resources_ids).count()

        return count

    class Meta:
        queryset = Tag.objects.all().order_by('name')
        resource_name = 'keywords'
        allowed_methods = ['get']
        filtering = {
            'slug': ALL,
        }


class RegionResource(TypeFilteredResource):

    """Regions api"""

    def dehydrate_count(self, bundle):
        count = 0
        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.published.all()
        else:
            resources = get_objects_for_user(
                bundle.request.user,
                'base.view_resourcebase'
            )
        if settings.RESOURCE_PUBLISHING:
            resources = resources.filter(is_published=True)

        resources_ids = resources.values_list('id', flat=True)

        if self.type_filter:
            count = bundle.obj.resourcebase_set.filter(
                id__in=resources_ids).instance_of(self.type_filter).count()
        else:
            count = bundle.obj.resourcebase_set.filter(id__in=resources_ids).count()

        return count

    class Meta:
        queryset = Region.objects.all().order_by('name')
        resource_name = 'regions'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
        }


class TopicCategoryResource(TypeFilteredResource):

    """Category api"""

    def dehydrate_count(self, bundle):
        resources = bundle.obj.resourcebase_set.all()
        if settings.RESOURCE_PUBLISHING:
            resources = resources.filter(is_published=True)
        if self.type_filter:
            resources = resources.instance_of(self.type_filter)
        if self.title_filter:
            resources = resources.filter(title__icontains=self.title_filter)
        if not settings.SKIP_PERMS_FILTER:
            permitted = get_objects_for_user(
                bundle.request.user,
                'base.view_resourcebase').values_list(
                'id',
                flat=True)
            resources = resources.filter(id__in=permitted)

        return resources.count()

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get']
        filtering = {
            'identifier': ALL,
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
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values_list('id', flat=True)).distinct().count()

    def dehydrate_maps_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').instance_of(Map)
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values_list('id', flat=True)).distinct().count()

    def dehydrate_documents_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').instance_of(Document)
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values_list('id', flat=True)).distinct().count()

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
        authentication = SessionAuthentication()
        resource_name = 'profiles'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
        }

REQUESTER_TYPES = {
    'commercial': 'commercial',
    'noncommercial': 'noncommercial',
    'academe': 'academe',
}



class DataRequestProfileResource(ModelResource):
    """Data Request Profile api"""
    data_request_detail_url = fields.CharField()
    org_type = fields.CharField()
    req_type = fields.CharField()
    status = fields.CharField()
    status_label = fields.CharField()
    is_rejected = fields.BooleanField(default=False)
    rejection_reason = fields.CharField()
    date_submitted = fields.CharField()
    shapefile_thumbnail_url = fields.CharField(null=True)

    class Meta:
        authorization = DataRequestAuthorization()
        authentication = SessionAuthentication()
        queryset = DataRequestProfile.objects.all().order_by('-key_created_date')
        resource_name = 'data_requests'
        allowed_methods = ['get']
        ordering = ['key_created_date', ]
        filtering = {'first_name': ALL,
                     'requester_type': ALL,
                     'request_status': ALL,
                     'organization': ALL,
                     'request_status': ALL,
                     'key_created_date': ALL,
                     }

    def dehydrate_data_request_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_org_type(self, bundle):
        return bundle.obj.get_organization_type_display()

    def dehydrate_rejection_reason(self, bundle):
        return bundle.obj.rejection_reason

    def dehydrate_status(self, bundle):
        return bundle.obj.get_request_status_display()

    def dehydrate_is_rejected(self, bundle):
        return bundle.obj.request_status == 'rejected'

    def dehydrate_date_submitted(self, bundle):
        return formats.date_format(bundle.obj.key_created_date, "SHORT_DATETIME_FORMAT")

    def dehydrate_status_label(self, bundle):
        if bundle.obj.request_status == 'pending' or bundle.obj.request_status == 'cancelled' or bundle.obj.request_status == 'unconfirmed':
            return 'default'
        elif bundle.obj.request_status == 'rejected':
            return 'danger'
        else:
            return 'success'

    def dehydrate_shapefile_thumbnail_url(self, bundle):
        if bundle.obj.jurisdiction_shapefile:
            return bundle.obj.jurisdiction_shapefile.thumbnail_url
        else:
            return None

    def apply_filters(self, request, applicable_filters):
        base_object_list = super(DataRequestProfileResource, self).apply_filters(request, applicable_filters)

        query = request.GET.get('title__icontains', None)
        if query:
            query = query.split(' ')
            q = Q()
            for t in query:
                q = q | Q(first_name__icontains=t)
                q = q | Q(middle_name__icontains=t)
                q = q | Q(last_name__icontains=t)
                q = q | Q(organization__icontains=t)
            base_object_list = base_object_list.filter(q).distinct()

        return base_object_list

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
