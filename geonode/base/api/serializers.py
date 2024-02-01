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
import logging
from slugify import slugify
from urllib.parse import urljoin
import json
import warnings

from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from geonode.people import Roles
from django.http import QueryDict

from deprecated import deprecated
from rest_framework import serializers
from rest_framework_gis import fields
from rest_framework.reverse import reverse, NoReverseMatch
from rest_framework.exceptions import ParseError

from dynamic_rest.serializers import DynamicEphemeralSerializer, DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField, DynamicComputedField

from avatar.templatetags.avatar_tags import avatar_url
from geonode.utils import bbox_swap
from geonode.base.api.exceptions import InvalidResourceException

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
    ThesaurusKeywordLabel,
    ExtraMetadata,
    LinkedResource,
)
from geonode.documents.models import Document
from geonode.geoapps.models import GeoApp
from geonode.groups.models import GroupCategory, GroupProfile
from geonode.base.api.fields import ComplexDynamicRelationField
from geonode.layers.utils import get_dataset_download_handlers, get_default_dataset_download_handler
from geonode.utils import build_absolute_uri
from geonode.security.utils import get_resources_with_perms, get_geoapp_subtypes
from geonode.resource.models import ExecutionRequest
from django.contrib.gis.geos import Polygon

logger = logging.getLogger(__name__)


class BaseDynamicModelSerializer(DynamicModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not isinstance(data, int):
            try:
                path = reverse(self.Meta.view_name)
                if not path.endswith("/"):
                    path = f"{path}/"
                url = urljoin(path, str(instance.pk))
                data["link"] = build_absolute_uri(url)
            except (TypeError, NoReverseMatch) as e:
                logger.exception(e)
        return data


class ResourceBaseToRepresentationSerializerMixin(DynamicModelSerializer):
    def to_representation(self, instance):
        request = self.context.get("request")
        data = super(ResourceBaseToRepresentationSerializerMixin, self).to_representation(instance)
        if request:
            data["perms"] = (
                instance.get_user_perms(request.user)
                .union(instance.get_self_resource().get_user_perms(request.user))
                .union(instance.get_real_instance().get_user_perms(request.user))
            )
            if not request.user.is_anonymous and getattr(settings, "FAVORITE_ENABLED", False):
                favorite = Favorite.objects.filter(user=request.user, object_id=instance.pk).count()
                data["favorite"] = favorite > 0
        # Adding links to resource_base api
        obj_id = data.get("pk", None)
        if obj_id:
            dehydrated = []
            link_fields = ["extension", "link_type", "name", "mime", "url"]

            links = Link.objects.filter(
                resource_id=int(obj_id), link_type__in=["OGC:WMS", "OGC:WFS", "OGC:WCS", "image", "metadata"]
            )
            for lnk in links:
                formatted_link = model_to_dict(lnk, fields=link_fields)
                dehydrated.append(formatted_link)
            if len(dehydrated) > 0:
                data["links"] = dehydrated
        return data


class ResourceBaseTypesSerializer(DynamicEphemeralSerializer):
    name = serializers.CharField()
    count = serializers.IntegerField()

    class Meta:
        name = "resource-types"


class PermSpecSerialiazer(DynamicEphemeralSerializer):
    class Meta:
        name = "perm-spec"

    class PermSpecFieldSerialiazer(DynamicEphemeralSerializer):
        perm_spec = serializers.ListField()

    users = PermSpecFieldSerialiazer(many=True)
    groups = PermSpecFieldSerialiazer(many=True)


class GroupSerializer(DynamicModelSerializer):
    class Meta:
        model = Group
        name = "group"
        fields = ("pk", "name")


class GroupProfileSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = GroupProfile
        name = "group_profile"
        view_name = "group-profiles-list"
        fields = ("pk", "title", "group", "slug", "logo", "description", "email", "keywords", "access", "categories")

    group = DynamicRelationField(GroupSerializer, embed=True, many=False)
    keywords = serializers.SlugRelatedField(many=True, slug_field="slug", read_only=True)
    categories = serializers.SlugRelatedField(many=True, slug_field="slug", queryset=GroupCategory.objects.all())


class SimpleHierarchicalKeywordSerializer(DynamicModelSerializer):
    class Meta:
        model = HierarchicalKeyword
        name = "HierarchicalKeyword"
        fields = ("name", "slug")

    def to_representation(self, value):
        return {"name": value.name, "slug": value.slug}


class _ThesaurusKeywordSerializerMixIn:
    def to_representation(self, value):
        _i18n = {}
        for _i18n_label in ThesaurusKeywordLabel.objects.filter(keyword__id=value.id).iterator():
            _i18n[_i18n_label.lang] = _i18n_label.label
        return {
            "name": value.alt_label,
            "slug": slugify(value.about),
            "uri": value.about,
            "thesaurus": {
                "name": value.thesaurus.title,
                "slug": value.thesaurus.identifier,
                "uri": value.thesaurus.about,
            },
            "i18n": _i18n,
        }


class SimpleThesaurusKeywordSerializer(_ThesaurusKeywordSerializerMixIn, DynamicModelSerializer):
    class Meta:
        model = ThesaurusKeyword
        name = "ThesaurusKeyword"
        fields = ("alt_label",)


class SimpleRegionSerializer(DynamicModelSerializer):
    class Meta:
        model = Region
        name = "Region"
        fields = ("code", "name")


class SimpleTopicCategorySerializer(DynamicModelSerializer):
    class Meta:
        model = TopicCategory
        name = "TopicCategory"
        fields = ("identifier", "gn_description")


class RestrictionCodeTypeSerializer(DynamicModelSerializer):
    class Meta:
        model = RestrictionCodeType
        name = "RestrictionCodeType"
        fields = ("identifier",)


class LicenseSerializer(DynamicModelSerializer):
    class Meta:
        model = License
        name = "License"
        fields = ("identifier",)


class SpatialRepresentationTypeSerializer(DynamicModelSerializer):
    class Meta:
        model = SpatialRepresentationType
        name = "SpatialRepresentationType"
        fields = ("identifier",)


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
        if _instance and hasattr(_instance, "embed_url") and _instance.embed_url != NotImplemented:
            return build_absolute_uri(_instance.embed_url)
        else:
            return ""


class DetailUrlField(DynamicComputedField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return build_absolute_uri(instance.detail_url)


class ExtraMetadataSerializer(DynamicModelSerializer):
    class Meta:
        model = ExtraMetadata
        name = "ExtraMetadata"
        fields = ("pk", "metadata")

    def to_representation(self, obj):
        if isinstance(obj, QuerySet):
            out = []
            for el in obj:
                out.append({**{"id": el.id}, **el.metadata})
            return out
        elif isinstance(obj, list):
            return obj
        return {**{"id": obj.id}, **obj.metadata}


class ThumbnailUrlField(DynamicComputedField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        thumbnail_url = instance.thumbnail_url

        return build_absolute_uri(thumbnail_url)


class DownloadLinkField(DynamicComputedField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @deprecated(version="4.2.0", reason="Will be replaced by download_urls")
    def get_attribute(self, instance):
        try:
            logger.info(
                "This field is deprecated, and will be removed in the future GeoNode version. Please refer to download_urls"
            )
            _instance = instance.get_real_instance()
            return _instance.download_url if hasattr(_instance, "download_url") else None
        except Exception as e:
            logger.exception(e)
            return None


class DownloadArrayLinkField(DynamicComputedField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        try:
            _instance = instance.get_real_instance()
        except Exception as e:
            logger.exception(e)
            raise e
        if _instance.resource_type in ["map"] + get_geoapp_subtypes():
            return []
        elif _instance.resource_type in ["document"]:
            return [
                {
                    "url": _instance.download_url,
                    "ajax_safe": _instance.download_is_ajax_safe,
                }
            ]
        elif _instance.resource_type in ["dataset"]:
            download_urls = []
            # lets get only the default one first to set it
            default_handler = get_default_dataset_download_handler()
            obj = default_handler(self.context.get("request"), _instance.alternate)
            if obj.download_url:
                download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": True})
            # then let's prepare the payload with everything
            handler_list = get_dataset_download_handlers()
            for handler in handler_list:
                obj = handler(self.context.get("request"), _instance.alternate)
                if obj.download_url:
                    download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": False})
            return download_urls
        else:
            return []


class FavoriteField(DynamicComputedField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        _user = self.context.get("request")
        if _user and not _user.user.is_anonymous:
            return Favorite.objects.filter(object_id=instance.pk, user=_user.user).exists()
        return False


class UserSerializer(BaseDynamicModelSerializer):
    class Meta:
        ref_name = "UserProfile"
        model = get_user_model()
        name = "user"
        view_name = "users-list"
        fields = ("pk", "username", "first_name", "last_name", "avatar", "perms", "is_superuser", "is_staff", "email")

    @classmethod
    def setup_eager_loading(cls, queryset):
        """Perform necessary eager loading of data."""
        queryset = queryset.prefetch_related()
        return queryset

    def to_representation(self, instance):
        # Dehydrate users private fields
        request = self.context.get("request")
        data = super().to_representation(instance)
        if not request or not request.user or not request.user.is_authenticated:
            if "perms" in data:
                del data["perms"]
        elif not request.user.is_superuser and not request.user.is_staff:
            if data["username"] != request.user.username:
                if "perms" in data:
                    del data["perms"]
        return data

    avatar = AvatarUrlField(240, read_only=True)


class ContactRoleField(DynamicComputedField):
    default_error_messages = {
        "required": ("ContactRoleField This field is required."),
    }

    def __init__(self, contact_type, **kwargs):
        self.contact_type = contact_type
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return getattr(instance, self.contact_type)

    def to_representation(self, value):
        return [UserSerializer(embed=True, many=False).to_representation(v) for v in value]

    def get_pks_of_users_to_set(self, value):
        pks_of_users_to_set = []
        for val in value:
            # make it possible to set contact roles via username or pk through API
            if "username" in val and "pk" in val:
                pk = val["pk"]
                username = val["username"]
                pk_user = get_user_model().objects.get(pk=pk)
                username_user = get_user_model().objects.get(username=username)
                if pk_user.pk != username_user.pk:
                    raise ParseError(
                        detail=f"user with pk: {pk} and username: {username} is not the same ... ", code=403
                    )
                pks_of_users_to_set.append(pk)
            elif "username" in val:
                username = val["username"]
                username_user = get_user_model().objects.get(username=[username])
                pks_of_users_to_set.append(username_user.pk)
            elif "pk" in val:
                pks_of_users_to_set.append(val["pk"])
        return pks_of_users_to_set

    def to_internal_value(self, value):
        return get_user_model().objects.filter(pk__in=self.get_pks_of_users_to_set(value))


class ExtentBboxField(DynamicComputedField):
    def get_attribute(self, instance):
        return instance.ll_bbox

    def to_representation(self, value):
        bbox = bbox_swap(value[:-1])
        return super().to_representation({"coords": bbox, "srid": value[-1]})


class DataBlobField(DynamicRelationField):
    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


class DataBlobSerializer(DynamicModelSerializer):
    class Meta:
        model = ResourceBase
        fields = ("pk", "blob")

    def to_representation(self, value):
        data = ResourceBase.objects.filter(id=value)
        if data.exists() and data.count() == 1:
            return data.get().blob
        return {}


class ResourceExecutionRequestSerializer(DynamicModelSerializer):
    class Meta:
        model = ResourceBase
        fields = ("pk",)

    def to_representation(self, instance):
        data = []
        request = self.context.get("request", None)
        if (
            request
            and request.user
            and not request.user.is_anonymous
            and ResourceBase.objects.filter(pk=instance).count() == 1
        ):
            _resource = ResourceBase.objects.get(pk=instance)
            executions = ExecutionRequest.objects.filter(
                Q(user=request.user)
                & ~Q(status=ExecutionRequest.STATUS_FINISHED)
                & (
                    (
                        Q(input_params__uuid=_resource.uuid)
                        | Q(output_params__output__uuid=_resource.uuid)
                        | Q(geonode_resource=_resource)
                    )
                )
            ).order_by("-created")

            for execution in executions:
                data.append(
                    {
                        "exec_id": execution.exec_id,
                        "user": execution.user.username,
                        "status": execution.status,
                        "func_name": execution.func_name,
                        "created": execution.created,
                        "finished": execution.finished,
                        "last_updated": execution.last_updated,
                        "input_params": execution.input_params,
                        "output_params": execution.output_params,
                        "status_url": urljoin(
                            settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": execution.exec_id})
                        ),
                    },
                )
        return data


api_bbox_settable_resource_models = [Document, GeoApp]


class ResourceBaseSerializer(
    ResourceBaseToRepresentationSerializerMixin,
    BaseDynamicModelSerializer,
):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        self.fields["pk"] = serializers.CharField(read_only=True)
        self.fields["uuid"] = serializers.CharField(read_only=True)
        self.fields["resource_type"] = serializers.CharField(required=False)
        self.fields["polymorphic_ctype_id"] = serializers.CharField(read_only=True)
        self.fields["owner"] = DynamicRelationField(UserSerializer, embed=True, many=False, read_only=True)
        self.fields["metadata_author"] = ContactRoleField(Roles.METADATA_AUTHOR.name, required=False)
        self.fields["processor"] = ContactRoleField(Roles.PROCESSOR.name, required=False)
        self.fields["publisher"] = ContactRoleField(Roles.PUBLISHER.name, required=False)
        self.fields["custodian"] = ContactRoleField(Roles.CUSTODIAN.name, required=False)
        self.fields["poc"] = ContactRoleField(Roles.POC.name, required=False)
        self.fields["distributor"] = ContactRoleField(Roles.DISTRIBUTOR.name, required=False)
        self.fields["resource_user"] = ContactRoleField(Roles.RESOURCE_USER.name, required=False)
        self.fields["resource_provider"] = ContactRoleField(Roles.RESOURCE_PROVIDER.name, required=False)
        self.fields["originator"] = ContactRoleField(Roles.ORIGINATOR.name, required=False)
        self.fields["principal_investigator"] = ContactRoleField(Roles.PRINCIPAL_INVESTIGATOR.name, required=False)
        self.fields["title"] = serializers.CharField(required=False)
        self.fields["abstract"] = serializers.CharField(required=False)
        self.fields["attribution"] = serializers.CharField(required=False)
        self.fields["doi"] = serializers.CharField(required=False)
        self.fields["alternate"] = serializers.CharField(read_only=True, required=False)
        self.fields["date"] = serializers.DateTimeField(required=False)
        self.fields["date_type"] = serializers.CharField(required=False)
        self.fields["temporal_extent_start"] = serializers.DateTimeField(required=False)
        self.fields["temporal_extent_end"] = serializers.DateTimeField(required=False)
        self.fields["edition"] = serializers.CharField(required=False)
        self.fields["purpose"] = serializers.CharField(required=False)
        self.fields["maintenance_frequency"] = serializers.CharField(required=False)
        self.fields["constraints_other"] = serializers.CharField(required=False)
        self.fields["language"] = serializers.CharField(required=False)
        self.fields["supplemental_information"] = serializers.CharField(required=False)
        self.fields["data_quality_statement"] = serializers.CharField(required=False)
        self.fields["bbox_polygon"] = fields.GeometryField(read_only=True, required=False)
        self.fields["ll_bbox_polygon"] = fields.GeometryField(read_only=True, required=False)
        self.fields["extent"] = ExtentBboxField(required=False)
        self.fields["srid"] = serializers.CharField(required=False)
        self.fields["group"] = ComplexDynamicRelationField(GroupSerializer, embed=True, many=False)
        self.fields["popular_count"] = serializers.CharField(required=False)
        self.fields["share_count"] = serializers.CharField(required=False)
        self.fields["rating"] = serializers.CharField(required=False)
        self.fields["featured"] = serializers.BooleanField(required=False)
        self.fields["is_published"] = serializers.BooleanField(required=False, read_only=True)
        self.fields["is_approved"] = serializers.BooleanField(required=False, read_only=True)
        self.fields["detail_url"] = DetailUrlField(read_only=True)
        self.fields["created"] = serializers.DateTimeField(read_only=True)
        self.fields["last_updated"] = serializers.DateTimeField(read_only=True)
        self.fields["raw_abstract"] = serializers.CharField(read_only=True)
        self.fields["raw_purpose"] = serializers.CharField(read_only=True)
        self.fields["raw_constraints_other"] = serializers.CharField(read_only=True)
        self.fields["raw_supplemental_information"] = serializers.CharField(read_only=True)
        self.fields["raw_data_quality_statement"] = serializers.CharField(read_only=True)
        self.fields["metadata_only"] = serializers.BooleanField(required=False)
        self.fields["processed"] = serializers.BooleanField(read_only=True)
        self.fields["state"] = serializers.CharField(read_only=True)
        self.fields["sourcetype"] = serializers.CharField(read_only=True)
        self.fields["embed_url"] = EmbedUrlField(required=False)
        self.fields["thumbnail_url"] = ThumbnailUrlField(read_only=True)
        self.fields["keywords"] = ComplexDynamicRelationField(
            SimpleHierarchicalKeywordSerializer, embed=False, many=True
        )
        self.fields["tkeywords"] = ComplexDynamicRelationField(SimpleThesaurusKeywordSerializer, embed=False, many=True)
        self.fields["regions"] = DynamicRelationField(SimpleRegionSerializer, embed=True, many=True, read_only=True)
        self.fields["category"] = ComplexDynamicRelationField(SimpleTopicCategorySerializer, embed=True, many=False)
        self.fields["restriction_code_type"] = ComplexDynamicRelationField(
            RestrictionCodeTypeSerializer, embed=True, many=False
        )
        self.fields["license"] = ComplexDynamicRelationField(LicenseSerializer, embed=True, many=False)
        self.fields["spatial_representation_type"] = ComplexDynamicRelationField(
            SpatialRepresentationTypeSerializer, embed=True, many=False
        )
        self.fields["blob"] = serializers.JSONField(required=False, write_only=True)
        self.fields["is_copyable"] = serializers.BooleanField(read_only=True)
        self.fields["download_url"] = DownloadLinkField(read_only=True)
        self.fields["favorite"] = FavoriteField(read_only=True)
        self.fields["download_urls"] = DownloadArrayLinkField(read_only=True)

    metadata = ComplexDynamicRelationField(ExtraMetadataSerializer, embed=False, many=True, deferred=True)

    class Meta:
        model = ResourceBase
        name = "resource"
        view_name = "base-resources-list"
        fields = (
            "pk",
            "uuid",
            "resource_type",
            "polymorphic_ctype_id",
            "perms",
            "owner",
            "poc",
            "metadata_author",
            "processor",
            "publisher",
            "custodian",
            "distributor",
            "resource_user",
            "resource_provider",
            "originator",
            "principal_investigator",
            "keywords",
            "tkeywords",
            "regions",
            "category",
            "title",
            "abstract",
            "attribution",
            "alternate",
            "doi",
            "bbox_polygon",
            "ll_bbox_polygon",
            "srid",
            "date",
            "date_type",
            "edition",
            "purpose",
            "maintenance_frequency",
            "restriction_code_type",
            "constraints_other",
            "license",
            "language",
            "spatial_representation_type",
            "temporal_extent_start",
            "temporal_extent_end",
            "supplemental_information",
            "data_quality_statement",
            "group",
            "popular_count",
            "share_count",
            "rating",
            "featured",
            "is_published",
            "is_approved",
            "detail_url",
            "embed_url",
            "created",
            "last_updated",
            "raw_abstract",
            "raw_purpose",
            "raw_constraints_other",
            "raw_supplemental_information",
            "raw_data_quality_statement",
            "metadata_only",
            "processed",
            "state",
            "data",
            "subtype",
            "sourcetype",
            "is_copyable",
            "blob",
            "metadata",
            "executions",
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
            "extent": {"required": False},
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
            "executions": {"required": False, "embed": False, "deferred": True, "read_only": True},
            "owner": {"required": False},
            "resource_type": {"required": False},
            "download_url": {"required": False},
            "is_copyable": {"required": False},
        }

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if "data" in data:
            data["blob"] = data.pop("data")
        if isinstance(data, QueryDict):
            data = data.dict()
        data = super(ResourceBaseSerializer, self).to_internal_value(data)
        return data

    def save(self, **kwargs):
        extent = self.validated_data.pop("extent", None)
        instance = super().save(**kwargs)
        if extent and instance.get_real_instance()._meta.model in api_bbox_settable_resource_models:
            srid = extent.get("srid", "EPSG:4326")
            coords = extent.get("coords")
            if not coords:
                logger.warning("BBOX was sent, but no coords were supplied. Skipping")
                return instance
            try:
                # small validation test
                Polygon.from_bbox(coords)
            except Exception as e:
                logger.exception(e)
                raise InvalidResourceException("The standard bbox provided is invalid")
            instance.set_bbox_polygon(coords, srid)
        return instance

    """
     - Deferred / not Embedded --> ?include[]=data
    """
    data = DataBlobField(
        DataBlobSerializer,
        source="id",
        many=False,
        embed=False,
        deferred=True,
        required=False,
    )

    """
     - Deferred / not Embedded --> ?include[]=executions
    """
    executions = DynamicRelationField(
        ResourceExecutionRequestSerializer,
        source="id",
        embed=False,
        deferred=True,
        required=False,
        read_only=True,
    )


class FavoriteSerializer(DynamicModelSerializer):
    resource = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        name = "favorites"
        fields = ("resource",)

    def to_representation(self, value):
        data = super().to_representation(value)
        return data["resource"]

    def get_resource(self, instance):
        resource = ResourceBase.objects.get(pk=instance.object_id)
        return ResourceBaseSerializer(resource).data


class BaseResourceCountSerializer(BaseDynamicModelSerializer):
    def to_representation(self, instance):
        request = self.context.get("request")
        filter_options = {}
        if request.query_params:
            filter_options = {
                "type_filter": request.query_params.get("type"),
                "title_filter": request.query_params.get("title__icontains"),
            }
        data = super().to_representation(instance)
        if not isinstance(data, int):
            try:
                count_filter = {self.Meta.count_type: instance}
                data["count"] = get_resources_with_perms(request.user, filter_options).filter(**count_filter).count()
            except (TypeError, NoReverseMatch) as e:
                logger.exception(e)
        return data


class HierarchicalKeywordSerializer(BaseResourceCountSerializer):
    class Meta:
        name = "keywords"
        model = HierarchicalKeyword
        count_type = "keywords"
        view_name = "keywords-list"
        fields = "__all__"


class ThesaurusKeywordSerializer(_ThesaurusKeywordSerializerMixIn, BaseResourceCountSerializer):
    class Meta:
        model = ThesaurusKeyword
        name = "tkeywords"
        view_name = "tkeywords-list"
        count_type = "tkeywords"
        fields = "__all__"


class RegionSerializer(BaseResourceCountSerializer):
    class Meta:
        name = "regions"
        model = Region
        count_type = "regions"
        view_name = "regions-list"
        fields = "__all__"


class TopicCategorySerializer(BaseResourceCountSerializer):
    class Meta:
        name = "categories"
        model = TopicCategory
        count_type = "category"
        view_name = "categories-list"
        fields = "__all__"


class OwnerSerializer(BaseResourceCountSerializer):
    class Meta:
        name = "owners"
        count_type = "owner"
        view_name = "owners-list"
        model = get_user_model()
        fields = ("pk", "username", "first_name", "last_name", "avatar", "perms")

    avatar = AvatarUrlField(240, read_only=True)


class SimpleResourceSerializer(DynamicModelSerializer):
    warnings.warn("SimpleResourceSerializer is deprecated", DeprecationWarning, stacklevel=2)

    class Meta:
        name = "linked_resources"
        model = ResourceBase
        fields = ("pk", "title", "resource_type", "detail_url", "thumbnail_url")

    def to_representation(self, instance: LinkedResource):
        return {
            "pk": instance.pk,
            "title": f"{'>>>' if instance.is_target else '<<<'} {instance.title}",
            "resource_type": instance.resource_type,
            "detail_url": instance.detail_url,
            "thumbnail_url": instance.thumbnail_url,
        }


class LinkedResourceSerializer(DynamicModelSerializer):
    def __init__(self, *kargs, serialize_source: bool = False, **kwargs):
        super().__init__(*kargs, **kwargs)
        self.serialize_target = not serialize_source

    class Meta:
        name = "linked_resources"
        model = LinkedResource
        fields = ("internal",)

    def to_representation(self, instance: LinkedResource):
        data = super().to_representation(instance)
        item: ResourceBase = instance.target if self.serialize_target else instance.source
        data.update(
            {
                "pk": item.pk,
                "title": item.title,
                "resource_type": item.resource_type,
                "detail_url": item.detail_url,
                "thumbnail_url": item.thumbnail_url,
            }
        )
        return data
