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
import json
from slugify import slugify
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework_gis import fields
from rest_framework.reverse import reverse, NoReverseMatch

from dynamic_rest.serializers import DynamicEphemeralSerializer, DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField, DynamicComputedField

from avatar.templatetags.avatar_tags import avatar_url

from geonode.favorite.models import Favorite
from geonode.base.models import (
    Link,
    ResourceBase,
    HierarchicalKeyword,
    Region,
    RestrictionCodeType,
    License,
    TopicCategory,
    SpatialRepresentationType,
    ThesaurusKeyword,
    ThesaurusKeywordLabel
)
from geonode.groups.models import (
    GroupCategory,
    GroupProfile)

from geonode.utils import build_absolute_uri
from geonode.security.utils import get_resources_with_perms

import logging

logger = logging.getLogger(__name__)


class BaseDynamicModelSerializer(DynamicModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not isinstance(data, int):
            try:
                path = reverse(self.Meta.view_name)
                if not path.endswith('/'):
                    path = f"{path}/"
                url = urljoin(path, str(instance.pk))
                data['link'] = build_absolute_uri(url)
            except (TypeError, NoReverseMatch) as e:
                logger.exception(e)
        return data


class ResourceBaseToRepresentationSerializerMixin(DynamicModelSerializer):

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super(ResourceBaseToRepresentationSerializerMixin, self).to_representation(instance)
        if request:
            data['perms'] = instance.get_user_perms(request.user).union(
                instance.get_self_resource().get_user_perms(request.user)
            )
            if not request.user.is_anonymous and getattr(settings, "FAVORITE_ENABLED", False):
                favorite = Favorite.objects.filter(user=request.user, object_id=instance.pk).count()
                data['favorite'] = favorite > 0
        # Adding links to resource_base api
        obj_id = data.get('pk', None)
        if obj_id:
            dehydrated = []
            link_fields = [
                'extension',
                'link_type',
                'name',
                'mime',
                'url'
            ]

            links = Link.objects.filter(
                resource_id=int(obj_id),
                link_type__in=['OGC:WMS', 'OGC:WFS', 'OGC:WCS', 'image', 'metadata']
            )
            for lnk in links:
                formatted_link = model_to_dict(lnk, fields=link_fields)
                dehydrated.append(formatted_link)
            if len(dehydrated) > 0:
                data['links'] = dehydrated
        return data


class ResourceBaseTypesSerializer(DynamicEphemeralSerializer):
    name = serializers.CharField()
    count = serializers.IntegerField()

    class Meta:
        name = 'resource-types'


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


class GroupProfileSerializer(BaseDynamicModelSerializer):

    class Meta:
        model = GroupProfile
        name = 'group_profile'
        view_name = 'group-profiles-list'
        fields = ('pk', 'title', 'group', 'slug', 'logo', 'description',
                  'email', 'keywords', 'access', 'categories')

    group = DynamicRelationField(GroupSerializer, embed=True, many=False)
    keywords = serializers.SlugRelatedField(many=True, slug_field='slug', read_only=True)
    categories = serializers.SlugRelatedField(
        many=True, slug_field='slug', queryset=GroupCategory.objects.all())


class SimpleHierarchicalKeywordSerializer(DynamicModelSerializer):

    class Meta:
        model = HierarchicalKeyword
        name = 'HierarchicalKeyword'
        fields = ('name', 'slug')

    def to_representation(self, value):
        return {'name': value.name, 'slug': value.slug}


class _ThesaurusKeywordSerializerMixIn:

    def to_representation(self, value):
        _i18n = {}
        for _i18n_label in ThesaurusKeywordLabel.objects.filter(keyword__id=value.id).iterator():
            _i18n[_i18n_label.lang] = _i18n_label.label
        return {
            'name': value.alt_label,
            'slug': slugify(value.about),
            'uri': value.about,
            'thesaurus': {
                'name': value.thesaurus.title,
                'slug': value.thesaurus.identifier,
                'uri': value.thesaurus.about
            },
            'i18n': _i18n
        }


class SimpleThesaurusKeywordSerializer(_ThesaurusKeywordSerializerMixIn, DynamicModelSerializer):

    class Meta:
        model = ThesaurusKeyword
        name = 'ThesaurusKeyword'
        fields = ('alt_label', )


class SimpleRegionSerializer(DynamicModelSerializer):

    class Meta:
        model = Region
        name = 'Region'
        fields = ('code', 'name')


class SimpleTopicCategorySerializer(DynamicModelSerializer):

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
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return build_absolute_uri(avatar_url(instance, self.avatar_size))


class EmbedUrlField(DynamicComputedField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        try:
            _instance = instance.get_real_instance()
        except Exception as e:
            logger.exception(e)
            _instance = None
        if _instance and hasattr(_instance, 'embed_url') and _instance.embed_url != NotImplemented:
            return build_absolute_uri(_instance.embed_url)
        else:
            return ""


class DetailUrlField(DynamicComputedField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return build_absolute_uri(instance.detail_url)


class ThumbnailUrlField(DynamicComputedField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        thumbnail_url = instance.thumbnail_url

        return build_absolute_uri(thumbnail_url)


class UserSerializer(BaseDynamicModelSerializer):

    class Meta:
        ref_name = 'UserProfile'
        model = get_user_model()
        name = 'user'
        view_name = 'users-list'
        fields = ('pk', 'username', 'first_name', 'last_name', 'avatar', 'perms', 'is_superuser', 'is_staff')

    @classmethod
    def setup_eager_loading(cls, queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related()
        return queryset

    def to_representation(self, instance):
        # Dehydrate users private fields
        request = self.context.get('request')
        data = super().to_representation(instance)
        if not request or not request.user or not request.user.is_authenticated:
            if 'perms' in data:
                del data['perms']
        elif not request.user.is_superuser and not request.user.is_staff:
            if data['username'] != request.user.username:
                if 'perms' in data:
                    del data['perms']
        return data

    avatar = AvatarUrlField(240, read_only=True)


class ContactRoleField(DynamicComputedField):

    def __init__(self, contat_type, **kwargs):
        self.contat_type = contat_type
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return getattr(instance, self.contat_type)

    def to_representation(self, value):
        return UserSerializer(embed=True, many=False).to_representation(value)


class DataBlobField(DynamicRelationField):

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


class DataBlobSerializer(DynamicModelSerializer):

    class Meta:
        model = ResourceBase
        fields = ('pk', 'blob')

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        data = ResourceBase.objects.filter(id=value)
        if data.exists() and data.count() == 1:
            return data.get().blob
        return {}


class ResourceBaseSerializer(
    ResourceBaseToRepresentationSerializerMixin,
    BaseDynamicModelSerializer,
):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        self.fields['pk'] = serializers.CharField(read_only=True)
        self.fields['uuid'] = serializers.CharField(read_only=True)
        self.fields['resource_type'] = serializers.CharField(required=False)
        self.fields['polymorphic_ctype_id'] = serializers.CharField(read_only=True)
        self.fields['owner'] = DynamicRelationField(UserSerializer, embed=True, many=False, read_only=True, required=False)
        self.fields['poc'] = ContactRoleField('poc', read_only=True)
        self.fields['metadata_author'] = ContactRoleField('metadata_author', read_only=True)
        self.fields['title'] = serializers.CharField()
        self.fields['abstract'] = serializers.CharField(required=False)
        self.fields['attribution'] = serializers.CharField(required=False)
        self.fields['doi'] = serializers.CharField(required=False)
        self.fields['alternate'] = serializers.CharField(read_only=True)
        self.fields['date'] = serializers.DateTimeField(required=False)
        self.fields['date_type'] = serializers.CharField(required=False)
        self.fields['temporal_extent_start'] = serializers.DateTimeField(required=False)
        self.fields['temporal_extent_end'] = serializers.DateTimeField(required=False)
        self.fields['edition'] = serializers.CharField(required=False)
        self.fields['purpose'] = serializers.CharField(required=False)
        self.fields['maintenance_frequency'] = serializers.CharField(required=False)
        self.fields['constraints_other'] = serializers.CharField(required=False)
        self.fields['language'] = serializers.CharField(required=False)
        self.fields['supplemental_information'] = serializers.CharField(required=False)
        self.fields['data_quality_statement'] = serializers.CharField(required=False)
        self.fields['bbox_polygon'] = fields.GeometryField(required=False)
        self.fields['ll_bbox_polygon'] = fields.GeometryField(required=False)
        self.fields['srid'] = serializers.CharField(required=False)
        self.fields['group'] = DynamicRelationField(GroupSerializer, embed=True, many=False)
        self.fields['popular_count'] = serializers.CharField(required=False)
        self.fields['share_count'] = serializers.CharField(required=False)
        self.fields['rating'] = serializers.CharField(required=False)
        self.fields['featured'] = serializers.BooleanField(required=False)
        self.fields['is_published'] = serializers.BooleanField(required=False)
        self.fields['is_approved'] = serializers.BooleanField(required=False)
        self.fields['detail_url'] = DetailUrlField(read_only=True)
        self.fields['created'] = serializers.DateTimeField(read_only=True)
        self.fields['last_updated'] = serializers.DateTimeField(read_only=True)
        self.fields['raw_abstract'] = serializers.CharField(read_only=True)
        self.fields['raw_purpose'] = serializers.CharField(read_only=True)
        self.fields['raw_constraints_other'] = serializers.CharField(read_only=True)
        self.fields['raw_supplemental_information'] = serializers.CharField(read_only=True)
        self.fields['raw_data_quality_statement'] = serializers.CharField(read_only=True)
        self.fields['metadata_only'] = serializers.BooleanField(required=False)
        self.fields['processed'] = serializers.BooleanField(read_only=True)
        self.fields['state'] = serializers.CharField(read_only=True)
        self.fields['sourcetype'] = serializers.CharField(read_only=True)

        self.fields['embed_url'] = EmbedUrlField(required=False)
        self.fields['thumbnail_url'] = ThumbnailUrlField(read_only=True)
        self.fields['keywords'] = DynamicRelationField(
            SimpleHierarchicalKeywordSerializer, embed=False, many=True)
        self.fields['tkeywords'] = DynamicRelationField(
            SimpleThesaurusKeywordSerializer, embed=False, many=True)
        self.fields['regions'] = DynamicRelationField(
            SimpleRegionSerializer, embed=True, many=True, read_only=True)
        self.fields['category'] = DynamicRelationField(
            SimpleTopicCategorySerializer, embed=True, many=False)
        self.fields['restriction_code_type'] = DynamicRelationField(
            RestrictionCodeTypeSerializer, embed=True, many=False)
        self.fields['license'] = DynamicRelationField(
            LicenseSerializer, embed=True, many=False)
        self.fields['spatial_representation_type'] = DynamicRelationField(
            SpatialRepresentationTypeSerializer, embed=True, many=False)

        self.fields['blob'] = serializers.JSONField(required=False, write_only=True)

    class Meta:
        model = ResourceBase
        name = 'resource'
        view_name = 'base-resources-list'
        fields = (
            'pk', 'uuid', 'resource_type', 'polymorphic_ctype_id', 'perms',
            'owner', 'poc', 'metadata_author',
            'keywords', 'tkeywords', 'regions', 'category',
            'title', 'abstract', 'attribution', 'alternate', 'doi', 'bbox_polygon', 'll_bbox_polygon', 'srid',
            'date', 'date_type', 'edition', 'purpose', 'maintenance_frequency',
            'restriction_code_type', 'constraints_other', 'license', 'language',
            'spatial_representation_type', 'temporal_extent_start', 'temporal_extent_end',
            'supplemental_information', 'data_quality_statement', 'group',
            'popular_count', 'share_count', 'rating', 'featured', 'is_published', 'is_approved',
            'detail_url', 'embed_url', 'created', 'last_updated',
            'raw_abstract', 'raw_purpose', 'raw_constraints_other',
            'raw_supplemental_information', 'raw_data_quality_statement', 'metadata_only', 'processed', 'state',
            'data', 'subtype', 'sourcetype',
            'blob',
            # TODO
            # csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry,
            # metadata_uploaded, metadata_uploaded_preserve, metadata_xml,
            # users_geolimits, groups_geolimits
        )
        extra_kwargs = {
            "abstract": {"required": False},
            "attribution": {"required": False},
            "doi": {"required": False},
            "date": {"required": False},
            "date_type": {"required": False},
            "temporal_extent_start": {"required": False},
            "temporal_extent_end": {"required": False},
            "edition": {"required": False},
            "purpose": {"required": False},
            "maintenance_frequency": {"required": False},
            "constraints_other": {"required": False},
            "language": {"required": False},
            "supplemental_information": {"required": False},
            "data_quality_statement": {"required": False},
            "bbox_polygon": {"required": False},
            "ll_bbox_polygon": {"required": False},
            "srid": {"required": False},
            "popular_count": {"required": False},
            "share_count": {"required": False},
            "rating": {"required": False},
            "featured": {"required": False},
            "is_published": {"required": False},
            "is_approved": {"required": False},
            "metadata_only": {"required": False},
            "embed_url": {"required": False},
            "thumbnail_url": {"required": False},
            "blob": {"required": False, "write_only": True},
            "owner": {"required": False},
            "resource_type": {"required": False}
        }

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if 'data' in data:
            data['blob'] = data.pop('data')
        data = super(ResourceBaseSerializer, self).to_internal_value(data)
        return data

    """
     - Deferred / not Embedded --> ?include[]=data
    """
    data = DataBlobField(
        DataBlobSerializer,
        source='id',
        many=False,
        embed=False,
        deferred=True,
        required=False,
    )


class FavoriteSerializer(DynamicModelSerializer):
    resource = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        name = 'favorites'
        fields = 'resource',

    def to_representation(self, value):
        data = super().to_representation(value)
        return data['resource']

    def get_resource(self, instance):
        resource = ResourceBase.objects.get(pk=instance.object_id)
        return ResourceBaseSerializer(resource).data


class BaseResourceCountSerializer(BaseDynamicModelSerializer):

    def to_representation(self, instance):
        request = self.context.get('request')
        filter_options = {}
        if request.query_params:
            filter_options = {
                'type_filter': request.query_params.get('type'),
                'title_filter': request.query_params.get('title__icontains')
            }
        data = super().to_representation(instance)
        if not isinstance(data, int):
            try:
                count_filter = {self.Meta.count_type: instance}
                data['count'] = get_resources_with_perms(
                    request.user, filter_options).filter(**count_filter).count()
            except (TypeError, NoReverseMatch) as e:
                logger.exception(e)
        return data


class HierarchicalKeywordSerializer(BaseResourceCountSerializer):

    class Meta:
        name = 'keywords'
        model = HierarchicalKeyword
        count_type = 'keywords'
        view_name = 'keywords-list'
        fields = '__all__'


class ThesaurusKeywordSerializer(_ThesaurusKeywordSerializerMixIn, BaseResourceCountSerializer):

    class Meta:
        model = ThesaurusKeyword
        name = 'tkeywords'
        view_name = 'tkeywords-list'
        count_type = 'tkeywords'
        fields = '__all__'


class RegionSerializer(BaseResourceCountSerializer):

    class Meta:
        name = 'regions'
        model = Region
        count_type = 'regions'
        view_name = 'regions-list'
        fields = '__all__'


class TopicCategorySerializer(BaseResourceCountSerializer):

    class Meta:
        name = 'categories'
        model = TopicCategory
        count_type = 'category'
        view_name = 'categories-list'
        fields = '__all__'


class OwnerSerializer(BaseResourceCountSerializer):

    class Meta:
        name = 'owners'
        count_type = 'owner'
        view_name = 'owners-list'
        model = get_user_model()
        fields = ('pk', 'username', 'first_name', 'last_name', 'avatar', 'perms')

    avatar = AvatarUrlField(240, read_only=True)
