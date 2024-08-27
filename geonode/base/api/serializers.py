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

from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from geonode.assets.utils import get_default_asset
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
from geonode.layers.utils import get_download_handlers, get_default_dataset_download_handler
from geonode.assets.handlers import asset_handler_registry
from geonode.utils import build_absolute_uri
from geonode.security.utils import get_resources_with_perms, get_geoapp_subtypes
from geonode.resource.models import ExecutionRequest
from django.contrib.gis.geos import Polygon

logger = logging.getLogger(__name__)


def user_serializer():
    import geonode.people.api.serializers as ser

    return ser.UserSerializer


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

                parents = []
                parent = self.parent
                while parent:
                    parents.append(type(parent).__name__)
                    parent = parent.parent

                logger.warning(
                    f"Deprecated: BaseDynamicModelSerializer should be replaced with proper Field"
                    f" - Parents: {parents} Root: {type(self).__name__}"
                )
            except (TypeError, NoReverseMatch) as e:
                logger.exception(e)
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
                f"Field {self.field_name} is deprecated and will be removed in the future GeoNode version. Please refer to download_urls"
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

        asset = get_default_asset(_instance)
        if asset is not None:
            asset_url = asset_handler_registry.get_handler(asset).create_download_url(asset)

        if _instance.resource_type in ["map"] + get_geoapp_subtypes():
            return []
        elif _instance.resource_type in ["document"]:
            payload = [
                {
                    "url": _instance.download_url,
                    "ajax_safe": _instance.download_is_ajax_safe,
                },
            ]
            if asset:
                payload.append({"url": asset_url, "ajax_safe": False, "default": False})
            return payload

        elif _instance.resource_type in ["dataset"]:
            download_urls = []
            # lets get only the default one first to set it
            default_handler = get_default_dataset_download_handler()
            obj = default_handler(self.context.get("request"), _instance.alternate)
            if obj.download_url:
                download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": True})
            # then let's prepare the payload with everything
            for handler in get_download_handlers():
                obj = handler(self.context.get("request"), _instance.alternate)
                if obj.download_url:
                    download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": False})

            if asset:
                download_urls.append({"url": asset_url, "ajax_safe": True, "default": False if download_urls else True})

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


class AutoLinkField(DynamicComputedField):

    def get_attribute(self, instance):
        parents = []
        parent = self.parent
        while parent:
            parents.append(type(parent).__name__)
            parent = parent.parent

        logger.debug(
            f"AutoLinkField reading Meta from first parent - Parents: {parents} root: {type(self.root).__name__}"
        )

        try:
            path = reverse(self.parent.Meta.view_name)
            if not path.endswith("/"):
                path = f"{path}/"
            url = urljoin(path, str(instance.pk))
            return build_absolute_uri(url)

        except AttributeError as e:
            logger.exception(f"Parents: {parents} root: {type(self.root).__name__}", exc_info=e)
            return None

        except Exception as e:
            logger.exception(e)
            return None


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
        return [user_serializer()(embed=True, many=False).to_representation(v) for v in value]

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


class LinkedResourceEmbeddedSerializer(DynamicModelSerializer):
    class Meta:
        model = ResourceBase
        fields = ("pk",)

    def to_representation(self, instance):
        from geonode.base.api.views import base_linked_resources_payload

        request = self.context.get("request", None)
        _resource = ResourceBase.objects.get(pk=instance)

        return (
            base_linked_resources_payload(_resource.get_real_instance(), request.user)
            if request and request.user and _resource
            else {}
        )


api_bbox_settable_resource_models = [Document, GeoApp]


class PermsSerializer(DynamicModelSerializer):
    class Meta:
        model = ResourceBase
        fields = ("pk",)

    def to_representation(self, instance):
        request = self.context.get("request", None)
        resource = ResourceBase.objects.get(pk=instance)
        return resource.get_user_perms(request.user) if request and request.user and resource else []


class LinksSerializer(DynamicModelSerializer):
    class Meta:
        model = ResourceBase

    def to_representation(self, instance):
        ret = []
        link_fields = ["extension", "link_type", "name", "mime", "url"]
        links = Link.objects.filter(
            resource_id=instance,  # link_type__in=["OGC:WMS", "OGC:WFS", "OGC:WCS", "image", "metadata"]
        )
        for lnk in links:
            formatted_link = model_to_dict(lnk, fields=link_fields)
            ret.append(formatted_link)
            if lnk.asset:
                extras = {
                    "type": "asset",
                    "content": model_to_dict(lnk.asset, ["title", "description", "type", "created"]),
                }
                extras["content"]["download_url"] = asset_handler_registry.get_handler(lnk.asset).create_download_url(
                    lnk.asset
                )
                formatted_link["extras"] = extras

        return ret


class ResourceManagementField(serializers.BooleanField):
    MAPPING = {"is_approved": "can_approve", "is_published": "can_publish", "featured": "can_feature"}

    def to_internal_value(self, data):
        new_val = super().to_internal_value(data)
        user = self.context["request"].user
        user_action = self.MAPPING.get(self.field_name)
        instance = self.root.instance or ResourceBase.objects.get(pk=self.root.initial_data["pk"])
        if getattr(user, user_action)(instance):
            logger.debug("User can perform the action, the new value is returned")
            return new_val
        else:
            logger.warning(f"The user does not have the perms to update the value of {self.field_name}")
            return getattr(instance, self.field_name)


class ResourceBaseSerializer(DynamicModelSerializer):
    pk = serializers.CharField(read_only=True)
    uuid = serializers.CharField(read_only=True)
    resource_type = serializers.CharField(required=False)
    polymorphic_ctype_id = serializers.CharField(read_only=True)
    owner = DynamicRelationField(user_serializer(), embed=True, read_only=True)
    metadata_author = ContactRoleField(Roles.METADATA_AUTHOR.name, required=False)
    processor = ContactRoleField(Roles.PROCESSOR.name, required=False)
    publisher = ContactRoleField(Roles.PUBLISHER.name, required=False)
    custodian = ContactRoleField(Roles.CUSTODIAN.name, required=False)
    poc = ContactRoleField(Roles.POC.name, required=False)
    distributor = ContactRoleField(Roles.DISTRIBUTOR.name, required=False)
    resource_user = ContactRoleField(Roles.RESOURCE_USER.name, required=False)
    resource_provider = ContactRoleField(Roles.RESOURCE_PROVIDER.name, required=False)
    originator = ContactRoleField(Roles.ORIGINATOR.name, required=False)
    principal_investigator = ContactRoleField(Roles.PRINCIPAL_INVESTIGATOR.name, required=False)
    title = serializers.CharField(required=False)
    abstract = serializers.CharField(required=False)
    attribution = serializers.CharField(required=False)
    doi = serializers.CharField(required=False)
    alternate = serializers.CharField(read_only=True, required=False)
    date = serializers.DateTimeField(required=False)
    date_type = serializers.CharField(required=False)
    temporal_extent_start = serializers.DateTimeField(required=False)
    temporal_extent_end = serializers.DateTimeField(required=False)
    edition = serializers.CharField(required=False)
    purpose = serializers.CharField(required=False)
    maintenance_frequency = serializers.CharField(required=False)
    constraints_other = serializers.CharField(required=False)
    language = serializers.CharField(required=False)
    supplemental_information = serializers.CharField(required=False)
    data_quality_statement = serializers.CharField(required=False)
    bbox_polygon = fields.GeometryField(read_only=True, required=False)
    ll_bbox_polygon = fields.GeometryField(read_only=True, required=False)
    extent = ExtentBboxField(required=False)
    srid = serializers.CharField(required=False)
    group = ComplexDynamicRelationField(GroupSerializer, embed=True)
    popular_count = serializers.CharField(required=False)
    share_count = serializers.CharField(required=False)
    rating = serializers.CharField(required=False)
    featured = ResourceManagementField(required=False)
    advertised = serializers.BooleanField(required=False)
    is_published = ResourceManagementField(required=False)
    is_approved = ResourceManagementField(required=False)
    detail_url = DetailUrlField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)
    raw_abstract = serializers.CharField(read_only=True)
    raw_purpose = serializers.CharField(read_only=True)
    raw_constraints_other = serializers.CharField(read_only=True)
    raw_supplemental_information = serializers.CharField(read_only=True)
    raw_data_quality_statement = serializers.CharField(read_only=True)
    metadata_only = serializers.BooleanField(required=False)
    processed = serializers.BooleanField(read_only=True)
    state = serializers.CharField(read_only=True)
    sourcetype = serializers.CharField(read_only=True)
    embed_url = EmbedUrlField(required=False)
    thumbnail_url = ThumbnailUrlField(read_only=True)
    keywords = ComplexDynamicRelationField(SimpleHierarchicalKeywordSerializer, many=True)
    tkeywords = ComplexDynamicRelationField(SimpleThesaurusKeywordSerializer, many=True)
    regions = DynamicRelationField(SimpleRegionSerializer, embed=True, many=True, read_only=True)
    category = ComplexDynamicRelationField(SimpleTopicCategorySerializer, embed=True)
    restriction_code_type = ComplexDynamicRelationField(RestrictionCodeTypeSerializer, embed=True)
    license = ComplexDynamicRelationField(LicenseSerializer, embed=True)
    spatial_representation_type = ComplexDynamicRelationField(SpatialRepresentationTypeSerializer, embed=True)
    blob = serializers.JSONField(required=False, write_only=True)
    is_copyable = serializers.BooleanField(read_only=True)
    download_url = DownloadLinkField(read_only=True)
    favorite = FavoriteField(read_only=True)
    download_urls = DownloadArrayLinkField(read_only=True)
    perms = DynamicRelationField(PermsSerializer, source="id", read_only=True)
    links = DynamicRelationField(LinksSerializer, source="id", read_only=True)

    # Deferred fields
    metadata = ComplexDynamicRelationField(ExtraMetadataSerializer, many=True, deferred=True)
    data = DataBlobField(DataBlobSerializer, source="id", deferred=True, required=False)
    executions = DynamicRelationField(
        ResourceExecutionRequestSerializer, source="id", deferred=True, required=False, read_only=True
    )
    linked_resources = DynamicRelationField(
        LinkedResourceEmbeddedSerializer, source="id", deferred=True, required=False, read_only=True
    )
    link = AutoLinkField(read_only=True)

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
            "advertised",
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
            "linked_resources",
            "download_url",
            "download_urls",
            "extent",
            "favorite",
            "thumbnail_url",
            "links",
            "link",
            "metadata_uploaded_preserve",
            # TODO
            # csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry,
            # metadata_uploaded, metadata_uploaded_preserve, metadata_xml,
            # users_geolimits, groups_geolimits
        )

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
