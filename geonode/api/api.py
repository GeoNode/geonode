# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import json
import time

from django.db.models import Q
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Count
from django.http.response import HttpResponse
from django.template.response import TemplateResponse
from django.utils.translation import get_language

from avatar.templatetags.avatar_tags import avatar_url
from tastypie import http
from tastypie.exceptions import BadRequest

from geonode import qgis_server, geoserver
from geonode.api.paginator import CrossSiteXHRPaginator
from geonode.api.authorization import GeoNodeStyleAuthorization, ApiLockdownAuthorization, \
    GroupAuthorization, GroupProfileAuthorization
from geonode.qgis_server.models import QGISServerStyle
from guardian.shortcuts import get_objects_for_user
from tastypie.bundle import Bundle

from geonode.base.models import ResourceBase
from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.base.models import HierarchicalKeyword
from geonode.base.models import ThesaurusKeywordLabel
from geonode.layers.models import Layer, Style
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile, GroupCategory
from django.core.serializers.json import DjangoJSONEncoder
from tastypie.serializers import Serializer
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash

from geonode.utils import check_ogc_backend
from geonode.security.utils import get_visible_resources

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

        resources = get_visible_resources(
            resources,
            options['user'],
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        if resources and resources.count() > 0:
            if options['title_filter']:
                resources = resources.filter(title__icontains=options['title_filter'])

            if options['type_filter']:
                _type_filter = options['type_filter']
                if not isinstance(_type_filter, str):
                    _type_filter = _type_filter.__name__.lower()
                resources = resources.filter(polymorphic_ctype__model=_type_filter)

        counts = list(resources.values(options['count_type']).annotate(count=Count(options['count_type'])))

        return dict([(c[options['count_type']], c['count']) for c in counts])

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        counts = self.get_resources_counts(options)
        if 'objects' in data:
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

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}
        self.type_filter = None
        self.title_filter = None

        orm_filters = super(TypeFilteredResource, self).build_filters(filters)

        if 'type' in filters and filters['type'] in FILTER_TYPES.keys():
            self.type_filter = FILTER_TYPES[filters['type']]
        else:
            self.type_filter = None
        if 'title__icontains' in filters:
            self.title_filter = filters['title__icontains']

        return orm_filters

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['title_filter'] = getattr(self, 'title_filter', None)
        options['type_filter'] = getattr(self, 'type_filter', None)
        options['user'] = request.user

        return super(TypeFilteredResource, self).serialize(request, data, format, options)


class TagResource(TypeFilteredResource):
    """Tags api"""

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['count_type'] = 'keywords'

        return super(TagResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = HierarchicalKeyword.objects.all().order_by('name')
        resource_name = 'keywords'
        allowed_methods = ['get']
        filtering = {
            'slug': ALL,
        }
        serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class ThesaurusKeywordResource(TypeFilteredResource):
    """ThesaurusKeyword api"""

    thesaurus_identifier = fields.CharField(null=False)
    label_id = fields.CharField(null=False)

    def build_filters(self, filters={}, ignore_bad_filters=False):
        """adds filtering by current language"""
        _filters = filters.copy()
        id = _filters.pop('id', None)
        orm_filters = super(ThesaurusKeywordResource, self).build_filters(_filters)

        if id is not None:
            orm_filters['keyword__id'] = id

        orm_filters['lang'] = _filters['lang'] if 'lang' in _filters else get_language()

        if 'thesaurus' in _filters:
            orm_filters['keyword__thesaurus__identifier'] = _filters['thesaurus']

        return orm_filters

    def serialize(self, request, data, format, options={}):
        options['count_type'] = 'tkeywords__id'

        return super(ThesaurusKeywordResource, self).serialize(request, data, format, options)

    def dehydrate_id(self, bundle):
        return bundle.obj.keyword.id

    def dehydrate_label_id(self, bundle):
        return bundle.obj.id

    def dehydrate_thesaurus_identifier(self, bundle):
        return bundle.obj.keyword.thesaurus.identifier

    class Meta:
        queryset = ThesaurusKeywordLabel.objects \
            .all() \
            .order_by('label') \
            .select_related('keyword') \
            .select_related('keyword__thesaurus')

        resource_name = 'thesaurus/keywords'
        allowed_methods = ['get']
        filtering = {
            'id': ALL,
            'label': ALL,
            'lang': ALL,
            'thesaurus': ALL,
        }
        serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class RegionResource(TypeFilteredResource):
    """Regions api"""

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['count_type'] = 'regions'

        return super(RegionResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = Region.objects.all().order_by('name')
        resource_name = 'regions'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
            'code': ALL,
        }
        if settings.API_INCLUDE_REGIONS_COUNT:
            serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class TopicCategoryResource(TypeFilteredResource):
    """Category api"""
    layers_count = fields.IntegerField(default=0)

    def dehydrate_layers_count(self, bundle):
        request = bundle.request
        obj_with_perms = get_objects_for_user(request.user,
                                              'base.view_resourcebase').filter(polymorphic_ctype__model='layer')
        filter_set = bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id'))

        if not settings.SKIP_PERMS_FILTER:
            filter_set = get_visible_resources(
                filter_set,
                request.user if request else None,
                admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
                unpublished_not_visible=settings.RESOURCE_PUBLISHING,
                private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        return filter_set.distinct().count()

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['count_type'] = 'category'

        return super(TopicCategoryResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get']
        filtering = {
            'identifier': ALL,
        }
        serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class GroupCategoryResource(TypeFilteredResource):
    detail_url = fields.CharField()
    member_count = fields.IntegerField()
    resource_counts = fields.CharField()

    class Meta:
        queryset = GroupCategory.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        filtering = {'slug': ALL,
                     'name': ALL}
        authorization = ApiLockdownAuthorization()

    def apply_filters(self, request, applicable_filters):
        filtered = super(
            GroupCategoryResource,
            self).apply_filters(
            request,
            applicable_filters)
        return filtered

    def dehydrate_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_member_count(self, bundle):
        request = bundle.request
        user = request.user
        filtered = bundle.obj.groups.all()
        if not user.is_authenticated or user.is_anonymous:
            filtered = filtered.exclude(access='private')
        elif not user.is_superuser:
            categories_ids = user.group_list_all().values('categories')
            filtered = filtered.filter(
                Q(id__in=categories_ids) |
                ~Q(access='private')
            )
        return filtered.count()

    def dehydrate(self, bundle):
        """Provide additional resource counts"""
        request = bundle.request
        counts = _get_resource_counts(
            request,
            resourcebase_filter_kwargs={
                'group__groupprofile__categories': bundle.obj
            }
        )
        bundle.data.update(resource_counts=counts)
        return bundle


class GroupProfileResource(ModelResource):
    categories = fields.ToManyField(
        GroupCategoryResource,
        'categories',
        full=True
    )
    member_count = fields.CharField()
    manager_count = fields.CharField()
    logo_url = fields.CharField()
    detail_url = fields.CharField()

    class Meta:
        queryset = GroupProfile.objects.all()
        resource_name = 'group_profile'
        allowed_methods = ['get']
        filtering = {
            'title': ALL,
            'slug': ALL,
            'categories': ALL_WITH_RELATIONS,
        }
        ordering = ['title', 'last_modified']
        authorization = GroupProfileAuthorization()

    def dehydrate_member_count(self, bundle):
        """Provide relative URL to the geonode UI's page on the group"""
        return bundle.obj.member_queryset().count()

    def dehydrate_manager_count(self, bundle):
        """Provide relative URL to the geonode UI's page on the group"""
        return bundle.obj.get_managers().count()

    def dehydrate_detail_url(self, bundle):
        """Return relative URL to the geonode UI's page on the group"""
        if bundle.obj.slug:
            return reverse('group_detail', args=[bundle.obj.slug])
        else:
            return None

    def dehydrate_logo_url(self, bundle):
        return bundle.obj.logo_url


class GroupResource(ModelResource):
    group_profile = fields.ToOneField(
        GroupProfileResource,
        'groupprofile',
        full=True,
        null=True,
        blank=True
    )
    resource_counts = fields.CharField()

    class Meta:
        queryset = Group.objects.exclude(groupprofile=None)
        resource_name = 'groups'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
            'title': ALL,
            'group_profile': ALL_WITH_RELATIONS,
        }
        ordering = ['name', 'last_modified']
        authorization = GroupAuthorization()

    def dehydrate(self, bundle):
        """Provide additional resource counts"""
        request = bundle.request
        counts = _get_resource_counts(
            request,
            resourcebase_filter_kwargs={'group': bundle.obj}
        )

        bundle.data.update(resource_counts=counts)
        return bundle

    def get_object_list(self, request):
        """
        Overridden in order to exclude the ``anoymous`` group from the list

        """

        qs = super(GroupResource, self).get_object_list(request)
        return qs.exclude(name="anonymous")


class ProfileResource(TypeFilteredResource):
    """Profile api"""
    avatar_100 = fields.CharField(null=True)
    profile_detail_url = fields.CharField()
    email = fields.CharField(default='')
    layers_count = fields.IntegerField(default=0)
    maps_count = fields.IntegerField(default=0)
    documents_count = fields.IntegerField(default=0)
    current_user = fields.BooleanField(default=False)
    activity_stream_url = fields.CharField(null=True)

    def build_filters(self, filters=None, ignore_bad_filters=False):
        """adds filtering by group functionality"""
        if filters is None:
            filters = {}

        orm_filters = super(ProfileResource, self).build_filters(filters)

        if 'group' in filters:
            orm_filters['group'] = filters['group']

        if 'name__icontains' in filters:
            orm_filters['username__icontains'] = filters['name__icontains']

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """filter by group if applicable by group functionality"""

        group = applicable_filters.pop('group', None)
        name = applicable_filters.pop('name__icontains', None)

        semi_filtered = super(
            ProfileResource,
            self).apply_filters(
            request,
            applicable_filters)

        if group is not None:
            semi_filtered = semi_filtered.filter(
                groupmember__group__slug=group)

        if name is not None:
            semi_filtered = semi_filtered.filter(
                profile__first_name__icontains=name)

        return semi_filtered

    def dehydrate_email(self, bundle):
        email = ''
        if bundle.request.user.is_superuser:
            email = bundle.obj.email

        return email

    def dehydrate_layers_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').filter(polymorphic_ctype__model='layer')
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_maps_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').filter(polymorphic_ctype__model='map')
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_documents_count(self, bundle):
        obj_with_perms = get_objects_for_user(bundle.request.user,
                                              'base.view_resourcebase').filter(polymorphic_ctype__model='document')
        return bundle.obj.resourcebase_set.filter(id__in=obj_with_perms.values('id')).distinct().count()

    def dehydrate_avatar_100(self, bundle):
        return avatar_url(bundle.obj, 240)

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

    def dehydrate(self, bundle):
        """
        Protects user's personal information from non staff
        """
        is_owner = bundle.request.user == bundle.obj
        is_admin = bundle.request.user.is_staff or bundle.request.user.is_superuser
        if not (is_owner or is_admin):
            bundle.data = dict(
                id=bundle.data.get('id', ''),
                username=bundle.data.get('username', ''),
                first_name=bundle.data.get('first_name', ''),
                last_name=bundle.data.get('last_name', ''),
                avatar_100=bundle.data.get('avatar_100', ''),
                profile_detail_url=bundle.data.get('profile_detail_url', ''),
                documents_count=bundle.data.get('documents_count', 0),
                maps_count=bundle.data.get('maps_count', 0),
                layers_count=bundle.data.get('layers_count', 0),
            )
        return bundle

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

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['count_type'] = 'owner'

        return super(ProfileResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = get_user_model().objects.exclude(Q(username='AnonymousUser') | Q(is_active=False))
        resource_name = 'profiles'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
        }
        serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class OwnersResource(TypeFilteredResource):
    """Owners api, lighter and faster version of the profiles api"""
    full_name = fields.CharField(null=True)

    def dehydrate_full_name(self, bundle):
        return bundle.obj.get_full_name() or bundle.obj.username

    def dehydrate_email(self, bundle):
        email = ''
        if bundle.request.user.is_superuser:
            email = bundle.obj.email
        return email

    def dehydrate(self, bundle):
        """
        Protects user's personal information from non staff
        """
        is_owner = bundle.request.user == bundle.obj
        is_admin = bundle.request.user.is_staff or bundle.request.user.is_superuser
        if not (is_owner or is_admin):
            bundle.data = dict(id=bundle.obj.id, username=bundle.obj)
        return bundle

    def serialize(self, request, data, format, options=None):
        if options is None:
            options = {}
        options['count_type'] = 'owner'

        return super(OwnersResource, self).serialize(request, data, format, options)

    class Meta:
        queryset = get_user_model().objects.exclude(username='AnonymousUser')
        resource_name = 'owners'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
        }
        serializer = CountJSONSerializer()
        authorization = ApiLockdownAuthorization()


class QGISStyleResource(ModelResource):
    """Styles API for QGIS Server backend."""

    body = fields.CharField(attribute='body', use_in='detail')
    name = fields.CharField(attribute='name')
    title = fields.CharField(attribute='title')
    layer = fields.ForeignKey(
        'geonode.api.resourcebase_api.LayerResource',
        attribute='layer',
        null=True)
    style_url = fields.CharField(attribute='style_url')
    type = fields.CharField(attribute='type')

    class Meta:
        paginator_class = CrossSiteXHRPaginator
        queryset = QGISServerStyle.objects.all()
        resource_name = 'styles'
        detail_uri_name = 'id'
        allowed_methods = ['get', 'post', 'delete']
        authorization = GeoNodeStyleAuthorization()
        filtering = {
            'id': ALL,
            'title': ALL,
            'name': ALL,
            'layer': ALL_WITH_RELATIONS
        }

    def populate_object(self, style):
        """Populate results with necessary fields

        :param style: Style objects
        :type style: QGISServerStyle
        :return:
        """
        try:
            qgis_layer = style.layer_styles.first()
            """:type: geonode.qgis_server.QGISServerLayer"""
            style.layer = qgis_layer.layer
            style.type = 'qml'
        except Exception:
            pass
        return style

    def build_filters(self, filters=None, **kwargs):
        """Apply custom filters for layer."""
        filters = super(QGISStyleResource, self).build_filters(
            filters, **kwargs)
        # Convert layer__ filters into layer_styles__layer__
        updated_filters = {}
        for key, value in filters.items():
            key = key.replace('layer__', 'layer_styles__layer__')
            updated_filters[key] = value
        return updated_filters

    def build_bundle(self, obj=None, data=None, request=None, **kwargs):
        """Override build_bundle method to add additional info."""

        if obj is None and self._meta.object_class:
            obj = self._meta.object_class()

        elif obj:
            obj = self.populate_object(obj)

        return Bundle(
            obj=obj,
            data=data,
            request=request,
            **kwargs)

    def post_list(self, request, **kwargs):
        """Attempt to redirect to QGIS Server Style management.

        A post method should have the following field:

        name: Slug name of style
        title: Title of style
        style: the style file uploaded

        Also, should have kwargs:

        layername or layer__name: The layer name associated with the style

        or

        layer__id: The layer id associated with the style

        """
        from geonode.qgis_server.views import qml_style

        # Extract layer name information
        POST = request.POST
        FILES = request.FILES
        layername = POST.get('layername') or POST.get('layer__name')
        if not layername:
            layer_id = POST.get('layer__id')
            layer = Layer.objects.get(id=layer_id)
            layername = layer.name

        # move style file
        FILES['qml'] = FILES['style']

        response = qml_style(request, layername)

        if isinstance(response, TemplateResponse):
            if response.status_code == 201:
                obj = QGISServerStyle.objects.get(
                    layer_styles__layer__name=layername,
                    name=POST['name'])
                updated_bundle = self.build_bundle(obj=obj, request=request)
                location = self.get_resource_uri(updated_bundle)

                if not self._meta.always_return_data:
                    return http.HttpCreated(location=location)
                else:
                    updated_bundle = self.full_dehydrate(updated_bundle)
                    updated_bundle = self.alter_detail_data_to_serialize(
                        request, updated_bundle)
                    return self.create_response(
                        request, updated_bundle,
                        response_class=http.HttpCreated,
                        location=location)
            else:
                context = response.context_data
                # Check form valid
                style_upload_form = context['style_upload_form']
                if not style_upload_form.is_valid():
                    raise BadRequest(style_upload_form.errors.as_text())
                alert_message = context['alert_message']
                raise BadRequest(alert_message)
        elif isinstance(response, HttpResponse):
            response_class = None
            if response.status_code == 403:
                response_class = http.HttpForbidden
            return self.error_response(
                request, response.content,
                response_class=response_class)

    def delete_detail(self, request, **kwargs):
        """Attempt to redirect to QGIS Server Style management."""
        from geonode.qgis_server.views import qml_style
        style_id = kwargs.get('id')

        qgis_style = QGISServerStyle.objects.get(id=style_id)
        layername = qgis_style.layer_styles.first().layer.name

        response = qml_style(request, layername, style_name=qgis_style.name)

        if isinstance(response, TemplateResponse):
            if response.status_code == 200:
                # style deleted
                return http.HttpNoContent()
            else:
                context = response.context_data
                # Check form valid
                style_upload_form = context['style_upload_form']
                if not style_upload_form.is_valid():
                    raise BadRequest(style_upload_form.errors.as_text())
                alert_message = context['alert_message']
                raise BadRequest(alert_message)
        elif isinstance(response, HttpResponse):
            response_class = None
            if response.status_code == 403:
                response_class = http.HttpForbidden
            return self.error_response(
                request, response.content,
                response_class=response_class)

    def delete_list(self, request, **kwargs):
        """Do not allow delete list"""
        return http.HttpForbidden()


class GeoserverStyleResource(ModelResource):
    """Styles API for Geoserver backend."""
    body = fields.CharField(
        attribute='sld_body',
        use_in='detail')
    name = fields.CharField(attribute='name')
    title = fields.CharField(attribute='sld_title')
    # layer_default_style is polymorphic, so it will have many to many
    # relation
    layer = fields.ManyToManyField(
        'geonode.api.resourcebase_api.LayerResource',
        attribute='layer_default_style',
        null=True)
    version = fields.CharField(
        attribute='sld_version',
        null=True,
        blank=True)
    style_url = fields.CharField(attribute='sld_url')
    workspace = fields.CharField(attribute='workspace', null=True)
    type = fields.CharField(attribute='type')

    class Meta:
        paginator_class = CrossSiteXHRPaginator
        queryset = Style.objects.all()
        resource_name = 'styles'
        detail_uri_name = 'id'
        authorization = GeoNodeStyleAuthorization()
        allowed_methods = ['get']
        filtering = {
            'id': ALL,
            'title': ALL,
            'name': ALL,
            'layer': ALL_WITH_RELATIONS
        }

    def build_filters(self, filters=None, **kwargs):
        """Apply custom filters for layer."""
        filters = super(GeoserverStyleResource, self).build_filters(
            filters, **kwargs)
        # Convert layer__ filters into layer_styles__layer__
        updated_filters = {}
        for key, value in filters.items():
            key = key.replace('layer__', 'layer_default_style__')
            updated_filters[key] = value
        return updated_filters

    def populate_object(self, style):
        """Populate results with necessary fields

        :param style: Style objects
        :type style: Style
        :return:
        """
        style.type = 'sld'
        return style

    def build_bundle(self, obj=None, data=None, request=None, **kwargs):
        """Override build_bundle method to add additional info."""

        if obj is None and self._meta.object_class:
            obj = self._meta.object_class()

        elif obj:
            obj = self.populate_object(obj)

        return Bundle(
            obj=obj,
            data=data,
            request=request,
            **kwargs)


if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    class StyleResource(QGISStyleResource):
        """Wrapper for Generic Style Resource"""
        pass
elif check_ogc_backend(geoserver.BACKEND_PACKAGE):
    class StyleResource(GeoserverStyleResource):
        """Wrapper for Generic Style Resource"""
        pass


def _get_resource_counts(request, resourcebase_filter_kwargs):
    """Return a dict with counts of resources of various types

    The ``resourcebase_filter_kwargs`` argument should be a dict with a suitable
    queryset filter that can be applied to select only the relevant
    ``ResourceBase`` objects to use when retrieving counts. For example::

        _get_resource_counts(
            request,
            {
                'group__slug': 'my-group',
            }
        )

    The above function call would result in only counting ``ResourceBase``
    objects that belong to the group that has ``my-group`` as slug

    """
    resources = get_visible_resources(
        ResourceBase.objects.filter(**resourcebase_filter_kwargs),
        request.user,
        request=request,
        admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
        unpublished_not_visible=settings.RESOURCE_PUBLISHING,
        private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

    values = resources.values(
        'polymorphic_ctype__model',
        'is_approved',
        'is_published',
    )
    qs = values.annotate(counts=Count('polymorphic_ctype__model'))
    types = [
        'layer',
        'document',
        'map',
        'all'
    ]
    counts = {}
    for type_ in types:
        counts[type_] = {
            'total': 0,
            'visible': 0,
            'published': 0,
            'approved': 0,
        }
    for record in qs:
        resource_type = record['polymorphic_ctype__model']
        is_visible = all((record['is_approved'], record['is_published']))
        counts['all']['total'] += record['counts']
        counts['all']['visible'] += record['counts'] if is_visible else 0
        counts['all']['published'] += record['counts'] if record['is_published'] else 0
        counts['all']['approved'] += record['counts'] if record['is_approved'] else 0
        section = counts.get(resource_type)
        if section is not None:
            section['total'] += record['counts']
            section['visible'] += record['counts'] if is_visible else 0
            section['published'] += record['counts'] if record['is_published'] else 0
            section['approved'] += record['counts'] if record['is_approved'] else 0
    return counts
