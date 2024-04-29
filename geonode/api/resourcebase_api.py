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
from geonode.base.enumerations import LAYER_TYPES
import logging

from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
from tastypie.authentication import MultiAuthentication, SessionAuthentication
from tastypie.bundle import Bundle

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields

from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from tastypie.utils.mime import build_content_type

from geonode import get_version, geoserver
from geonode.layers.models import Dataset
from geonode.maps.models import Map
from geonode.geoapps.models import GeoApp
from geonode.documents.models import Document
from geonode.base.models import ResourceBase
from geonode.base.models import HierarchicalKeyword
from geonode.base.bbox_utils import filter_bbox
from geonode.groups.models import GroupProfile
from geonode.utils import check_ogc_backend
from geonode.security.utils import get_visible_resources
from .authentication import OAuthAuthentication
from .authorization import GeoNodeAuthorization, GeonodeApiKeyAuthentication

from .api import (
    TagResource,
    RegionResource,
    OwnersResource,
    ThesaurusKeywordResource,
    TopicCategoryResource,
    GroupResource,
    FILTER_TYPES,
)
from .paginator import CrossSiteXHRPaginator
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class CommonMetaApi:
    authorization = GeoNodeAuthorization()
    allowed_methods = ["get"]
    filtering = {
        "title": ALL,
        "keywords": ALL_WITH_RELATIONS,
        "tkeywords": ALL_WITH_RELATIONS,
        "regions": ALL_WITH_RELATIONS,
        "category": ALL_WITH_RELATIONS,
        "group": ALL_WITH_RELATIONS,
        "owner": ALL_WITH_RELATIONS,
        "date": ALL,
        "purpose": ALL,
        "uuid": ALL_WITH_RELATIONS,
        "abstract": ALL,
        "metadata": ALL_WITH_RELATIONS,
    }
    ordering = ["date", "title", "popular_count"]
    max_limit = None


class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, "keywords", null=True)
    regions = fields.ToManyField(RegionResource, "regions", null=True)
    category = fields.ToOneField(TopicCategoryResource, "category", null=True, full=True)
    group = fields.ToOneField(GroupResource, "group", null=True, full=True)
    owner = fields.ToOneField(OwnersResource, "owner", full=True)
    tkeywords = fields.ToManyField(ThesaurusKeywordResource, "tkeywords", null=True)
    VALUES = [
        # fields in the db
        "id",
        "uuid",
        "name",
        "typename",
        "title",
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
        "data_quality_statement",
        "abstract",
        "csw_wkt_geometry",
        "csw_type",
        "owner__username",
        "share_count",
        "popular_count",
        "srid",
        "bbox_polygon",
        "category__gn_description",
        "supplemental_information",
        "site_url",
        "thumbnail_url",
        "detail_url",
        "rating",
        "group__name",
        "has_time",
        "is_approved",
        "is_published",
        "dirty_state",
        "metadata_only",
    ]

    def build_filters(self, filters=None, ignore_bad_filters=False, **kwargs):
        if filters is None:
            filters = {}
        orm_filters = super().build_filters(filters=filters, ignore_bad_filters=ignore_bad_filters, **kwargs)
        if "type__in" in filters and (filters["type__in"] in FILTER_TYPES.keys() or filters["type__in"] in LAYER_TYPES):
            orm_filters.update({"type": filters.getlist("type__in")})
        if "app_type__in" in filters:
            orm_filters.update({"resource_type": filters["app_type__in"].lower()})

        _metadata = {f"metadata__{_k}": _v for _k, _v in filters.items() if _k.startswith("metadata__")}
        if _metadata:
            orm_filters.update({"metadata_filters": _metadata})

        if "extent" in filters:
            orm_filters.update({"extent": filters["extent"]})
        orm_filters["f_method"] = filters["f_method"] if "f_method" in filters else "and"
        if not settings.SEARCH_RESOURCES_EXTENDED:
            return self._remove_additional_filters(orm_filters)
        return orm_filters

    def _remove_additional_filters(self, orm_filters):
        orm_filters.pop("abstract__icontains", None)
        orm_filters.pop("purpose__icontains", None)
        orm_filters.pop("f_method", None)
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        types = applicable_filters.pop("type", None)
        extent = applicable_filters.pop("extent", None)
        keywords = applicable_filters.pop("keywords__slug__in", None)
        metadata_only = applicable_filters.pop("metadata_only", False)
        filtering_method = applicable_filters.pop("f_method", "and")
        metadata_filters = applicable_filters.pop("metadata_filters", None)
        if filtering_method == "or":
            filters = Q()
            for f in applicable_filters.items():
                filters |= Q(f)
            semi_filtered = self.get_object_list(request).filter(filters)
        else:
            semi_filtered = super().apply_filters(request, applicable_filters)
        filtered = None
        if types:
            for the_type in types:
                if the_type in LAYER_TYPES:
                    super_type = the_type
                    if "vector_time" == the_type:
                        super_type = "vector"
                    if filtered:
                        if "time" in the_type:
                            filtered = filtered | semi_filtered.filter(Layer___subtype=super_type).exclude(
                                Layer___has_time=False
                            )
                        else:
                            filtered = filtered | semi_filtered.filter(Layer___subtype=super_type)
                    else:
                        if "time" in the_type:
                            filtered = semi_filtered.filter(Layer___subtype=super_type).exclude(Layer___has_time=False)
                        else:
                            filtered = semi_filtered.filter(Layer___subtype=super_type)
                else:
                    _type_filter = FILTER_TYPES[the_type].__name__.lower()
                    if filtered:
                        filtered = filtered | semi_filtered.filter(polymorphic_ctype__model=_type_filter)
                    else:
                        filtered = semi_filtered.filter(polymorphic_ctype__model=_type_filter)
        else:
            filtered = semi_filtered

        if extent:
            filtered = filter_bbox(filtered, extent)

        if keywords:
            filtered = self.filter_h_keywords(filtered, keywords)

        if metadata_filters:
            filtered = filtered.filter(**metadata_filters)

        # return filtered
        return get_visible_resources(
            filtered,
            request.user if request else None,
            metadata_only=metadata_only,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )

    def filter_h_keywords(self, queryset, keywords):
        treeqs = HierarchicalKeyword.objects.none()
        if keywords and len(keywords) > 0:
            for keyword in keywords:
                try:
                    kws = HierarchicalKeyword.objects.filter(Q(name__iexact=keyword) | Q(slug__iexact=keyword))
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except ObjectDoesNotExist:
                    # Ignore keywords not actually used?
                    pass
            filtered = queryset.filter(Q(keywords__in=treeqs))
        else:
            filtered = queryset
        return filtered

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        # impossible.
        base_bundle = self.build_bundle(request=request)
        objects = self.obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(
            request.GET,
            sorted_objects,
            resource_uri=self.get_resource_uri(),
            limit=self._meta.limit,
            max_limit=self._meta.max_limit,
            collection_name=self._meta.collection_name,
        )
        to_be_serialized = paginator.page()

        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)

        return self.create_response(request, to_be_serialized, response_objects=objects)

    def format_objects(self, objects):
        """
        Format the objects for output in a response.
        """
        for key in ("site_url", "has_time"):
            if key in self.VALUES:
                idx = self.VALUES.index(key)
                del self.VALUES[idx]

        # hack needed because dehydrate does not seem to work in CommonModelApi
        formatted_objects = []
        for obj in objects:
            formatted_obj = model_to_dict(obj, fields=self.VALUES)
            if "site_url" not in formatted_obj or len(formatted_obj["site_url"]) == 0:
                formatted_obj["site_url"] = settings.SITEURL

            formatted_obj["owner__username"] = obj.owner.username
            formatted_obj["owner_name"] = obj.owner.get_full_name() or obj.owner.username

            if formatted_obj.get("metadata", None):
                formatted_obj["metadata"] = [model_to_dict(_m) for _m in formatted_obj["metadata"]]

            formatted_obj["detail_url"] = obj.detail_url

            formatted_objects.append(formatted_obj)

        return formatted_objects

    def create_response(self, request, data, response_class=HttpResponse, response_objects=None, **response_kwargs):
        """
        Extracts the common "which-format/serialize/return-response" cycle.

        Mostly a useful shortcut/hook.
        """

        # If an user does not have at least view permissions, he won't be able
        # to see the resource at all.
        filtered_objects_ids = None
        try:
            if data["objects"]:
                filtered_objects_ids = [
                    item.id
                    for item in data["objects"]
                    if request.user.has_perm("view_resourcebase", item.get_self_resource())
                ]
        except Exception:
            pass

        if isinstance(data, dict) and "objects" in data and not isinstance(data["objects"], list):
            if filtered_objects_ids:
                data["objects"] = [
                    x for x in list(self.format_objects(data["objects"])) if x["id"] in filtered_objects_ids
                ]
            else:
                data["objects"] = list(self.format_objects(data["objects"]))

            # give geonode version
            data["geonode_version"] = get_version()

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)

        return response_class(content=serialized, content_type=build_content_type(desired_format), **response_kwargs)

    def prepend_urls(self):
        return []

    def hydrate_title(self, bundle):
        title = bundle.data.get("title", None)
        if title:
            bundle.data["title"] = title.replace(",", "_")
        return bundle


class ResourceBaseResource(CommonModelApi):
    """ResourceBase api"""

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        queryset = ResourceBase.objects.polymorphic_queryset().distinct().order_by("-date")
        resource_name = "base"
        excludes = ["csw_anytext", "metadata_xml"]
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )


class FeaturedResourceBaseResource(CommonModelApi):
    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        queryset = ResourceBase.objects.filter(featured=True).order_by("-date")
        resource_name = "featured"
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )


class LayerResource(CommonModelApi):
    """Dataset API"""

    links = fields.ListField(attribute="links", null=True, use_in="all", default=[])
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        default_style = fields.ForeignKey("geonode.api.api.StyleResource", attribute="default_style", null=True)
        styles = fields.ManyToManyField("geonode.api.api.StyleResource", attribute="styles", null=True, use_in="detail")

    def build_filters(self, filters=None, ignore_bad_filters=False, **kwargs):
        _filters = filters.copy()
        metadata_only = _filters.pop("metadata_only", False)
        orm_filters = super().build_filters(_filters)
        orm_filters["metadata_only"] = False if not metadata_only else metadata_only[0]
        return orm_filters

    def format_objects(self, objects):
        """
        Formats the object.
        """
        formatted_objects = []
        for obj in objects:
            # convert the object to a dict using the standard values.
            # includes other values
            values = self.VALUES + ["alternate", "name"]
            formatted_obj = model_to_dict(obj, fields=values)
            username = obj.owner.get_username()
            full_name = obj.owner.get_full_name() or username
            formatted_obj["owner__username"] = username
            formatted_obj["owner_name"] = full_name
            if obj.category:
                formatted_obj["category__gn_description"] = _(obj.category.gn_description)
            if obj.group:
                formatted_obj["group"] = obj.group
                try:
                    formatted_obj["group_name"] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj["group_name"] = obj.group

            formatted_obj["keywords"] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj["regions"] = [r.name for r in obj.regions.all()] if obj.regions else []

            # provide style information
            bundle = self.build_bundle(obj=obj)
            formatted_obj["default_style"] = self.default_style.dehydrate(bundle, for_list=True)

            # Add resource uri
            formatted_obj["resource_uri"] = self.get_resource_uri(bundle)

            formatted_obj["links"] = self.dehydrate_ogc_links(bundle)

            if "site_url" not in formatted_obj or len(formatted_obj["site_url"]) == 0:
                formatted_obj["site_url"] = settings.SITEURL

            # Probe Remote Services
            formatted_obj["store_type"] = "dataset"
            formatted_obj["online"] = True
            if hasattr(obj, "subtype"):
                formatted_obj["store_type"] = obj.subtype
                if obj.subtype in ["tileStore", "remote"] and hasattr(obj, "remote_service"):
                    if obj.remote_service:
                        formatted_obj["online"] = obj.remote_service.probe == 200
                    else:
                        formatted_obj["online"] = False

            formatted_obj["gtype"] = self.dehydrate_gtype(bundle)

            formatted_obj["processed"] = obj.instance_is_processed
            # put the object on the response stack
            formatted_objects.append(formatted_obj)
        return formatted_objects

    def _dehydrate_links(self, bundle, link_types=None):
        """Dehydrate links field."""

        dehydrated = []
        obj = bundle.obj
        link_fields = ["extension", "link_type", "name", "mime", "url"]

        links = obj.link_set.all()
        if link_types:
            links = links.filter(link_type__in=link_types)
        for lnk in links:
            formatted_link = model_to_dict(lnk, fields=link_fields)
            dehydrated.append(formatted_link)

        return dehydrated

    def dehydrate_links(self, bundle):
        return self._dehydrate_links(bundle)

    def dehydrate_ogc_links(self, bundle):
        return self._dehydrate_links(bundle, ["OGC:WMS", "OGC:WFS", "OGC:WCS"])

    def dehydrate_gtype(self, bundle):
        return bundle.obj.gtype

    def build_bundle(self, obj=None, data=None, request=None, **kwargs):
        """Override build_bundle method to add additional info."""

        if obj is None and self._meta.object_class:
            obj = self._meta.object_class()
        elif obj:
            obj = self.populate_object(obj)

        return Bundle(obj=obj, data=data, request=request, **kwargs)

    def populate_object(self, obj):
        """Populate results with necessary fields

        :param obj: Dataset obj
        :type obj: Dataset
        :return:
        """
        return obj

    # copy parent attribute before modifying
    VALUES = CommonModelApi.VALUES[:]
    VALUES.append("typename")

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        queryset = Dataset.objects.distinct().order_by("-date")
        resource_name = "datasets"
        detail_uri_name = "id"
        include_resource_uri = True
        allowed_methods = ["get", "patch"]
        excludes = ["csw_anytext", "metadata_xml"]
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )
        filtering = CommonMetaApi.filtering
        # Allow filtering using ID
        filtering.update({"id": ALL, "name": ALL, "alternate": ALL, "metadata_only": ALL})


class MapResource(CommonModelApi):
    """Maps API"""

    def build_filters(self, filters=None, ignore_bad_filters=False, **kwargs):
        _filters = filters.copy()
        metadata_only = _filters.pop("metadata_only", False)
        orm_filters = super().build_filters(_filters)
        orm_filters["metadata_only"] = False if not metadata_only else metadata_only[0]
        return orm_filters

    def format_objects(self, objects):
        """
        Formats the objects and provides reference to list of layers in map
        resources.

        :param objects: Map objects
        """
        formatted_objects = []
        for obj in objects:
            # convert the object to a dict using the standard values.
            formatted_obj = model_to_dict(obj, fields=self.VALUES)
            username = obj.owner.get_username()
            full_name = obj.owner.get_full_name() or username
            formatted_obj["owner__username"] = username
            formatted_obj["owner_name"] = full_name
            if obj.category:
                formatted_obj["category__gn_description"] = _(obj.category.gn_description)
            if obj.group:
                formatted_obj["group"] = obj.group
                try:
                    formatted_obj["group_name"] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj["group_name"] = obj.group

            formatted_obj["keywords"] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj["regions"] = [r.name for r in obj.regions.all()] if obj.regions else []

            if "site_url" not in formatted_obj or len(formatted_obj["site_url"]) == 0:
                formatted_obj["site_url"] = settings.SITEURL

            # Probe Remote Services
            formatted_obj["store_type"] = "map"
            formatted_obj["online"] = True

            # get map layers
            map_datasets = obj.maplayers
            formatted_datasets = []
            map_dataset_fields = ["id", "name", "ows_url", "local"]
            for layer in map_datasets.iterator():
                formatted_map_dataset = model_to_dict(layer, fields=map_dataset_fields)
                formatted_datasets.append(formatted_map_dataset)
            formatted_obj["layers"] = formatted_datasets

            formatted_objects.append(formatted_obj)
        return formatted_objects

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        queryset = Map.objects.distinct().order_by("-date")
        resource_name = "maps"
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )


class GeoAppResource(CommonModelApi):
    """GeoApps API"""

    def format_objects(self, objects):
        """
        Formats the objects and provides reference to list of layers in GeoApp
        resources.

        :param objects: GeoApp objects
        """
        formatted_objects = []
        for obj in objects:
            # convert the object to a dict using the standard values.
            formatted_obj = model_to_dict(obj, fields=self.VALUES)
            username = obj.owner.get_username()
            full_name = obj.owner.get_full_name() or username
            formatted_obj["owner__username"] = username
            formatted_obj["owner_name"] = full_name
            if obj.category:
                formatted_obj["category__gn_description"] = obj.category.gn_description
            if obj.group:
                formatted_obj["group"] = obj.group
                try:
                    formatted_obj["group_name"] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj["group_name"] = obj.group

            formatted_obj["keywords"] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj["regions"] = [r.name for r in obj.regions.all()] if obj.regions else []

            if "site_url" not in formatted_obj or len(formatted_obj["site_url"]) == 0:
                formatted_obj["site_url"] = settings.SITEURL

            # Probe Remote Services
            formatted_obj["store_type"] = "geoapp"
            formatted_obj["online"] = True

            formatted_objects.append(formatted_obj)
        return formatted_objects

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        filtering = CommonMetaApi.filtering
        filtering.update({"app_type": ALL})
        queryset = GeoApp.objects.distinct().order_by("-date")
        resource_name = "geoapps"
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )


class DocumentResource(CommonModelApi):
    """Documents API"""

    def build_filters(self, filters=None, ignore_bad_filters=False, **kwargs):
        _filters = filters.copy()
        metadata_only = _filters.pop("metadata_only", False)
        orm_filters = super().build_filters(_filters)
        orm_filters["metadata_only"] = False if not metadata_only else metadata_only[0]
        return orm_filters

    def format_objects(self, objects):
        """
        Formats the objects and provides reference to list of layers in map
        resources.

        :param objects: Map objects
        """
        formatted_objects = []
        for obj in objects:
            # convert the object to a dict using the standard values.
            formatted_obj = model_to_dict(obj, fields=self.VALUES)
            username = obj.owner.get_username()
            full_name = obj.owner.get_full_name() or username
            formatted_obj["owner__username"] = username
            formatted_obj["owner_name"] = full_name
            if obj.category:
                formatted_obj["category__gn_description"] = _(obj.category.gn_description)
            if obj.group:
                formatted_obj["group"] = obj.group
                try:
                    formatted_obj["group_name"] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj["group_name"] = obj.group

            formatted_obj["keywords"] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj["regions"] = [r.name for r in obj.regions.all()] if obj.regions else []

            if "site_url" not in formatted_obj or len(formatted_obj["site_url"]) == 0:
                formatted_obj["site_url"] = settings.SITEURL

            # Probe Remote Services
            formatted_obj["store_type"] = "dataset"
            formatted_obj["online"] = True

            formatted_objects.append(formatted_obj)
        return formatted_objects

    class Meta(CommonMetaApi):
        paginator_class = CrossSiteXHRPaginator
        filtering = CommonMetaApi.filtering
        filtering.update({"subtype": ALL})
        queryset = Document.objects.distinct().order_by("-date")
        resource_name = "documents"
        authentication = MultiAuthentication(
            SessionAuthentication(), OAuthAuthentication(), GeonodeApiKeyAuthentication()
        )
