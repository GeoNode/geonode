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

from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Count
from django.utils.translation import get_language

from avatar.templatetags.avatar_tags import avatar_url
from guardian.shortcuts import get_objects_for_user
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle

from geonode.base.models import ResourceBase
from geonode.base.models import TopicCategory
from geonode.base.models import Region
from geonode.base.models import HierarchicalKeyword
from geonode.base.models import ThesaurusKeywordLabel

from geonode.layers.models import Layer, Style, LayerFile
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile, GroupCategory

from django.core.serializers.json import DjangoJSONEncoder
from tastypie.serializers import Serializer
from tastypie import fields
from tastypie.resources import ModelResource, Resource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
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

    def build_filters(self, filters=None):
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


class ThesaurusKeywordResource(TypeFilteredResource):
    """ThesaurusKeyword api"""

    thesaurus_identifier = fields.CharField(null=False)
    label_id = fields.CharField(null=False)

    def build_filters(self, filters={}):
        """adds filtering by current language"""

        id = filters.pop('id', None)

        orm_filters = super(ThesaurusKeywordResource, self).build_filters(filters)

        if id is not None:
            orm_filters['keyword__id'] = id

        orm_filters['lang'] = filters['lang'] if 'lang' in filters else get_language()

        if 'thesaurus' in filters:
            orm_filters['keyword__thesaurus__identifier'] = filters['thesaurus']

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


class TopicCategoryResource(TypeFilteredResource):
    """Category api"""

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


class GroupCategoryResource(TypeFilteredResource):
    detail_url = fields.CharField()
    member_count = fields.IntegerField()

    class Meta:
        queryset = GroupCategory.objects.all()
        allowed_methods = ['get']
        include_resource_uri = False
        fields = ['name', 'slug']
        filtering = {'slug': ALL,
                     'name': ALL}

    def dehydrate_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_member_count(self, bundle):
        return bundle.obj.groups.all().count()


class GroupResource(ModelResource):
    """Groups api"""

    detail_url = fields.CharField()
    member_count = fields.IntegerField()
    manager_count = fields.IntegerField()
    categories = fields.ToManyField(GroupCategoryResource, 'categories', full=True)

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
            'title': ALL,
            'categories': ALL_WITH_RELATIONS,
        }
        ordering = ['title', 'last_modified']


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

    def build_filters(self, filters=None):
        """adds filtering by group functionality"""
        if filters is None:
            filters = {}

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
        queryset = get_user_model().objects.exclude(username='AnonymousUser')
        resource_name = 'profiles'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
        }
        serializer = CountJSONSerializer()


class OwnersResource(TypeFilteredResource):
    """Owners api, lighter and faster version of the profiles api"""

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


class GeoserverStyleResource(ModelResource):
    """Styles api for Geoserver backend."""

    class Meta:
        queryset = Style.objects.all()
        resource_name = 'styles'
        allowed_methods = ['get', 'post', 'put']
        ordering = ['layername']


class QGISStyleObject(object):

    def __init__(self, style_id=None, name=None, layer=None,
                 style_file=None, style_type='qml', style_url=None):
        # File name of QML style file
        self.name = name
        # Related layers
        if layer and len(layer) > 0:
            self.layer = layer[0]
        # File object of the style
        self.file = style_file
        # LayerFile id of QML style in upload session
        self.id = style_id
        # Extension type of this style
        # Currently only for qml
        self.type = style_type
        # Url of downloadable QML Style
        self.url = style_url


class QGISStyleResource(Resource):
    """Styles api for QGIS Server backend."""

    name = fields.CharField(attribute='name')
    layer = fields.ForeignKey(
        'geonode.api.resourcebase_api.LayerResource',
        attribute='layer')
    id = fields.IntegerField(attribute='id')
    type = fields.CharField(attribute='type')
    url = fields.CharField(attribute='url', null=True)
    file = fields.FileField(attribute='file')

    class Meta:
        resource_name = 'styles'
        detail_uri_name = 'id'
        object_class = QGISStyleObject
        authorization = Authorization()

    def _build_style_url(self, layerfile):
        """Build downloadable url for QML Style.

        :param layerfile: LayerFile object
        :type layerfile: geonode.layers.models.LayerFile

        :return: url
        """
        try:
            layer = Layer.objects.get(upload_session=layerfile.upload_session)
            layername = layer.name
            style_url = reverse(
                'qgis_server:download-qml',
                kwargs={'layername': layername})
        except Layer.DoesNotExist:
            # There exists a stale layerfile
            return None
        return style_url

    def _generate_result(self, layerfiles):
        results = [
            QGISStyleObject(
                layer=lf.upload_session.layer_set.all(),
                style_id=lf.id,
                name=lf.file.name,
                style_file=lf.file,
                style_url=self._build_style_url(lf)) for lf in layerfiles
        ]
        results = [r for r in results if r.url]
        return results

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs[self._meta.detail_uri_name] = getattr(
                bundle_or_obj.obj, self._meta.detail_uri_name)
        else:
            kwargs[self._meta.detail_uri_name] = getattr(
                bundle_or_obj, self._meta.detail_uri_name)

        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        styles = []
        if 'layername' in kwargs:
            layername = kwargs.pop('layername')
            layer = Layer.objects.get(name=layername)
            styles = layer.upload_session.layerfile_set.filter(name='qml')
        if not kwargs.items():
            styles = LayerFile.objects.filter(name='qml')
        return self._generate_result(styles)

    def obj_get(self, bundle, **kwargs):
        styles = []
        if self._meta.detail_uri_name in kwargs:
            style_id = kwargs.pop(self._meta.detail_uri_name)
            styles = LayerFile.objects.filter(id=style_id)
        results = self._generate_result(styles)
        return results[0]

    def obj_create(self, bundle, **kwargs):
        bundle.obj = QGISStyleObject()
        bundle = self.full_hydrate(bundle)
        return bundle

    def obj_update(self, bundle, **kwargs):
        return self.obj_create(bundle, **kwargs)

    def obj_delete_list(self, bundle, **kwargs):
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, bundle, **kwargs):
        bucket = self._bucket()
        obj = bucket.get(kwargs['pk'])
        obj.delete()

    def deserialize(self, request, data, format=None):
        if not format:
            format = request.Meta.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            data = request.POST.copy()
            data.update(request.FILES)
            return data
        return super(QGISStyleResource, self).deserialize(
            request, data, format)

    def rollback(self, bundles):
        pass
