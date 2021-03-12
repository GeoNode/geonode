# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework_gis import fields
from dynamic_rest.serializers import DynamicEphemeralSerializer, DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField, DynamicComputedField

from urllib.parse import urljoin
from avatar.templatetags.avatar_tags import avatar_url

from geonode.base.models import (
    ResourceBase,
    HierarchicalKeyword,
    Region,
    RestrictionCodeType,
    License,
    TopicCategory,
    SpatialRepresentationType
)

from geonode.groups.models import GroupCategory, GroupProfile

import logging

logger = logging.getLogger(__name__)


class ResourceBaseTypesSerializer(DynamicEphemeralSerializer):

    class Meta:
        name = 'resource-type'

    resource_types = serializers.ListField()


class PermSpecSerialiazer(DynamicEphemeralSerializer):

    class Meta:
        name = 'perm-spec'

    class PermSpecFieldSerialiazer(DynamicEphemeralSerializer):
        perm_spec = serializers.ListField()

    users = PermSpecFieldSerialiazer(many=True)
    groups = PermSpecFieldSerialiazer(many=True)


class GroupSerializer(DynamicModelSerializer):

    class Meta:
        model = Group
        name = 'group'
        fields = ('pk', 'name')


class GroupProfileSerializer(DynamicModelSerializer):

    class Meta:
        model = GroupProfile
        name = 'group_profile'
        fields = ('pk', 'title', 'group', 'slug', 'logo', 'description',
                  'email', 'keywords', 'access', 'categories')

    group = DynamicRelationField(GroupSerializer, embed=True, many=False)
    keywords = serializers.SlugRelatedField(many=True, slug_field='slug', read_only=True)
    categories = serializers.SlugRelatedField(
        many=True, slug_field='slug', queryset=GroupCategory.objects.all())


class HierarchicalKeywordSerializer(DynamicModelSerializer):

    class Meta:
        model = HierarchicalKeyword
        name = 'HierarchicalKeyword'
        fields = ('name', 'slug')

    def to_representation(self, value):
        return {'name': value.name, 'slug': value.slug}


class RegionSerializer(DynamicModelSerializer):

    class Meta:
        model = Region
        name = 'Region'
        fields = ('code', 'name')


class TopicCategorySerializer(DynamicModelSerializer):

    class Meta:
        model = TopicCategory
        name = 'TopicCategory'
        fields = ('identifier',)


class RestrictionCodeTypeSerializer(DynamicModelSerializer):

    class Meta:
        model = RestrictionCodeType
        name = 'RestrictionCodeType'
        fields = ('identifier',)


class LicenseSerializer(DynamicModelSerializer):

    class Meta:
        model = License
        name = 'License'
        fields = ('identifier',)


class SpatialRepresentationTypeSerializer(DynamicModelSerializer):

    class Meta:
        model = SpatialRepresentationType
        name = 'SpatialRepresentationType'
        fields = ('identifier',)


class AvatarUrlField(DynamicComputedField):

    def __init__(self, avatar_size, **kwargs):
        self.avatar_size = avatar_size
        super(AvatarUrlField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        return avatar_url(instance, self.avatar_size)


class EmbedUrlField(DynamicComputedField):

    def __init__(self, **kwargs):
        super(EmbedUrlField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        _instance = instance.get_real_instance()
        if hasattr(_instance, 'embed_url') and _instance.embed_url != NotImplemented:
            return _instance.embed_url
        else:
            return ""


class ThumbnailUrlField(DynamicComputedField):

    def __init__(self, **kwargs):
        super(ThumbnailUrlField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        thumbnail_url = instance.thumbnail_url
        if hasattr(instance, 'curatedthumbnail'):
            try:
                if hasattr(instance.curatedthumbnail.img_thumbnail, 'url'):
                    thumbnail_url = instance.curatedthumbnail.thumbnail_url
            except Exception as e:
                logger.exception(e)

        if thumbnail_url and 'http' not in thumbnail_url:
            thumbnail_url = urljoin(settings.SITEURL, thumbnail_url)
        return thumbnail_url


class UserSerializer(DynamicModelSerializer):

    class Meta:
        ref_name = 'UserProfile'
        model = get_user_model()
        name = 'user'
        fields = ('pk', 'username', 'first_name', 'last_name', 'avatar')

    @classmethod
    def setup_eager_loading(cls, queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related()
        return queryset

    avatar = AvatarUrlField(240, read_only=True)


class ContactRoleField(DynamicComputedField):

    def __init__(self, contat_type, **kwargs):
        self.contat_type = contat_type
        super(ContactRoleField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        return getattr(instance, self.contat_type)

    def to_representation(self, value):
        return UserSerializer(embed=True, many=False).to_representation(value)


class ResourceBaseSerializer(DynamicModelSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(ResourceBaseSerializer, self).__init__(*args, **kwargs)

        self.fields['pk'] = serializers.CharField(read_only=True)
        self.fields['uuid'] = serializers.CharField(read_only=True)
        self.fields['resource_type'] = serializers.CharField(read_only=True)
        self.fields['polymorphic_ctype_id'] = serializers.CharField(read_only=True)
        self.fields['owner'] = DynamicRelationField(UserSerializer, embed=True, many=False, read_only=True)
        self.fields['poc'] = ContactRoleField('poc', read_only=True)
        self.fields['metadata_author'] = ContactRoleField('metadata_author', read_only=True)
        self.fields['title'] = serializers.CharField()
        self.fields['abstract'] = serializers.CharField()
        self.fields['attribution'] = serializers.CharField()
        self.fields['doi'] = serializers.CharField()
        self.fields['alternate'] = serializers.CharField(read_only=True)
        self.fields['date'] = serializers.DateTimeField()
        self.fields['date_type'] = serializers.CharField()
        self.fields['temporal_extent_start'] = serializers.DateTimeField()
        self.fields['temporal_extent_end'] = serializers.DateTimeField()
        self.fields['edition'] = serializers.CharField()
        self.fields['purpose'] = serializers.CharField()
        self.fields['maintenance_frequency'] = serializers.CharField()
        self.fields['constraints_other'] = serializers.CharField()
        self.fields['language'] = serializers.CharField()
        self.fields['supplemental_information'] = serializers.CharField()
        self.fields['data_quality_statement'] = serializers.CharField()
        self.fields['bbox_polygon'] = fields.GeometryField()
        self.fields['ll_bbox_polygon'] = fields.GeometryField()
        self.fields['srid'] = serializers.CharField()
        self.fields['group'] = DynamicRelationField(GroupSerializer, embed=True, many=False)
        self.fields['popular_count'] = serializers.CharField()
        self.fields['share_count'] = serializers.CharField()
        self.fields['rating'] = serializers.CharField()
        self.fields['featured'] = serializers.BooleanField()
        self.fields['is_published'] = serializers.BooleanField()
        self.fields['is_approved'] = serializers.BooleanField()
        self.fields['detail_url'] = serializers.CharField(read_only=True)
        self.fields['created'] = serializers.DateTimeField(read_only=True)
        self.fields['last_updated'] = serializers.DateTimeField(read_only=True)
        self.fields['raw_abstract'] = serializers.CharField(read_only=True)
        self.fields['raw_purpose'] = serializers.CharField(read_only=True)
        self.fields['raw_constraints_other'] = serializers.CharField(read_only=True)
        self.fields['raw_supplemental_information'] = serializers.CharField(read_only=True)
        self.fields['raw_data_quality_statement'] = serializers.CharField(read_only=True)

        self.fields['embed_url'] = EmbedUrlField()
        self.fields['thumbnail_url'] = ThumbnailUrlField()
        self.fields['keywords'] = DynamicRelationField(
            HierarchicalKeywordSerializer, embed=False, many=True)
        self.fields['regions'] = DynamicRelationField(
            RegionSerializer, embed=True, many=True, read_only=True)
        self.fields['category'] = DynamicRelationField(
            TopicCategorySerializer, embed=True, many=False)
        self.fields['restriction_code_type'] = DynamicRelationField(
            RestrictionCodeTypeSerializer, embed=True, many=False)
        self.fields['license'] = DynamicRelationField(
            LicenseSerializer, embed=True, many=False)
        self.fields['spatial_representation_type'] = DynamicRelationField(
            SpatialRepresentationTypeSerializer, embed=True, many=False)

    class Meta:
        model = ResourceBase
        name = 'resource'
        fields = (
            'pk', 'uuid', 'resource_type', 'polymorphic_ctype_id',
            'owner', 'poc', 'metadata_author',
            'keywords', 'regions', 'category',
            'title', 'abstract', 'attribution', 'doi', 'alternate', 'bbox_polygon', 'll_bbox_polygon', 'srid',
            'date', 'date_type', 'edition', 'purpose', 'maintenance_frequency',
            'restriction_code_type', 'constraints_other', 'license', 'language',
            'spatial_representation_type', 'temporal_extent_start', 'temporal_extent_end',
            'supplemental_information', 'data_quality_statement', 'group',
            'popular_count', 'share_count', 'rating', 'featured', 'is_published', 'is_approved',
            'detail_url', 'embed_url', 'created', 'last_updated',
            'raw_abstract', 'raw_purpose', 'raw_constraints_other',
            'raw_supplemental_information', 'raw_data_quality_statement'
            # TODO
            # csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry,
            # metadata_uploaded, metadata_uploaded_preserve, metadata_xml,
            # users_geolimits, groups_geolimits
        )
