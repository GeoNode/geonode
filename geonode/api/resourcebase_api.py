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
import re

from django.core.urlresolvers import resolve
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
from django.contrib.staticfiles.templatetags import staticfiles
from tastypie.authentication import MultiAuthentication, SessionAuthentication
from django.template.response import TemplateResponse
from tastypie import http
from tastypie.bundle import Bundle

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils import trailing_slash

from guardian.shortcuts import get_objects_for_user

from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from tastypie.utils.mime import build_content_type

from geonode import get_version, qgis_server, geoserver
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase
from geonode.base.models import HierarchicalKeyword
from geonode.people.models import Profile
from geonode.groups.models import GroupProfile
from geonode.utils import check_ogc_backend
from geonode.security.utils import get_visible_resources

from .authorization import GeoNodeAuthorization, GeonodeApiKeyAuthentication

from .api import TagResource, RegionResource, OwnersResource
from .api import ThesaurusKeywordResource
from .api import TopicCategoryResource, GroupResource
from .api import FILTER_TYPES

if settings.HAYSTACK_SEARCH:
    from haystack.query import SearchQuerySet  # noqa

LAYER_SUBTYPES = {
    'vector': 'dataStore',
    'raster': 'coverageStore',
    'remote': 'remoteStore',
    'vector_time': 'vectorTimeSeries',
}
FILTER_TYPES.update(LAYER_SUBTYPES)


class CommonMetaApi:
    authorization = GeoNodeAuthorization()
    allowed_methods = ['get']
    filtering = {'title': ALL,
                 'keywords': ALL_WITH_RELATIONS,
                 'tkeywords': ALL_WITH_RELATIONS,
                 'regions': ALL_WITH_RELATIONS,
                 'category': ALL_WITH_RELATIONS,
                 'group': ALL_WITH_RELATIONS,
                 'owner': ALL_WITH_RELATIONS,
                 'date': ALL,
                 }
    ordering = ['date', 'title', 'popular_count']
    max_limit = None


class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    regions = fields.ToManyField(RegionResource, 'regions', null=True)
    category = fields.ToOneField(
        TopicCategoryResource,
        'category',
        null=True,
        full=True)
    group = fields.ToOneField(
        GroupResource,
        'group',
        null=True,
        full=True)
    owner = fields.ToOneField(OwnersResource, 'owner', full=True)
    tkeywords = fields.ToManyField(
        ThesaurusKeywordResource, 'tkeywords', null=True)
    VALUES = [
        # fields in the db
        'id',
        'uuid',
        'title',
        'date',
        'date_type',
        'edition',
        'purpose',
        'maintenance_frequency',
        'restriction_code_type',
        'constraints_other',
        'license',
        'language',
        'spatial_representation_type',
        'temporal_extent_start',
        'temporal_extent_end',
        'data_quality_statement',
        'abstract',
        'csw_wkt_geometry',
        'csw_type',
        'owner__username',
        'share_count',
        'popular_count',
        'srid',
        'bbox_x0',
        'bbox_x1',
        'bbox_y0',
        'bbox_y1',
        'category__gn_description',
        'supplemental_information',
        'thumbnail_url',
        'detail_url',
        'rating',
        'group__name',
        'has_time',
        'is_approved',
        'is_published',
    ]

    def build_filters(self, filters=None, ignore_bad_filters=False, **kwargs):
        if filters is None:
            filters = {}
        orm_filters = super(CommonModelApi, self).build_filters(
            filters=filters, ignore_bad_filters=ignore_bad_filters, **kwargs)
        if 'type__in' in filters and filters[
                'type__in'] in FILTER_TYPES.keys():
            orm_filters.update({'type': filters.getlist('type__in')})
        if 'extent' in filters:
            orm_filters.update({'extent': filters['extent']})
        # Nothing returned if +'s are used instead of spaces for text search,
        # so swap them out. Must be a better way of doing this?
        for filter in orm_filters:
            if filter in ['title__contains', 'q']:
                orm_filters[filter] = orm_filters[filter].replace("+", " ")
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        types = applicable_filters.pop('type', None)
        extent = applicable_filters.pop('extent', None)
        keywords = applicable_filters.pop('keywords__slug__in', None)
        semi_filtered = super(
            CommonModelApi,
            self).apply_filters(
            request,
            applicable_filters)
        filtered = None
        if types:
            for the_type in types:
                if the_type in LAYER_SUBTYPES.keys():
                    super_type = the_type
                    if 'vector_time' == the_type:
                        super_type = 'vector'
                    if filtered:
                        if 'time' in the_type:
                            filtered = filtered | semi_filtered.filter(
                                Layer___storeType=LAYER_SUBTYPES[super_type]).exclude(Layer___has_time=False)
                        else:
                            filtered = filtered | semi_filtered.filter(
                                Layer___storeType=LAYER_SUBTYPES[super_type])
                    else:
                        if 'time' in the_type:
                            filtered = semi_filtered.filter(
                                Layer___storeType=LAYER_SUBTYPES[super_type]).exclude(Layer___has_time=False)
                        else:
                            filtered = semi_filtered.filter(
                                Layer___storeType=LAYER_SUBTYPES[super_type])
                else:
                    if filtered:
                        filtered = filtered | semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
                    else:
                        filtered = semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
        else:
            filtered = semi_filtered

        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            filtered = self.filter_published(filtered, request)

        if settings.GROUP_PRIVATE_RESOURCES:
            filtered = self.filter_group(filtered, request)

        if extent:
            filtered = self.filter_bbox(filtered, extent)

        if keywords:
            filtered = self.filter_h_keywords(filtered, keywords)

        return filtered

    def filter_published(self, queryset, request):
        filter_set = get_visible_resources(
            queryset,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING)

        return filter_set

    def filter_group(self, queryset, request):
        filter_set = get_visible_resources(
            queryset,
            request.user if request else None,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        return filter_set

    def filter_h_keywords(self, queryset, keywords):
        filtered = queryset
        treeqs = HierarchicalKeyword.objects.none()
        for keyword in keywords:
            try:
                kws = HierarchicalKeyword.objects.filter(Q(name__iexact=keyword) | Q(slug__iexact=keyword))
                for kw in kws:
                    treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
            except ObjectDoesNotExist:
                # Ignore keywords not actually used?
                pass

        filtered = queryset.filter(Q(keywords__in=treeqs))
        return filtered

    def filter_bbox(self, queryset, bbox):
        """
        modify the queryset q to limit to data that intersects with the
        provided bbox

        bbox - 4 tuple of floats representing 'southwest_lng,southwest_lat,
        northeast_lng,northeast_lat'
        returns the modified query
        """
        bbox = bbox.split(
            ',')  # TODO: Why is this different when done through haystack?
        bbox = map(str, bbox)  # 2.6 compat - float to decimal conversion
        intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) |
                       Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))

        return queryset.filter(intersects)

    def build_haystack_filters(self, parameters):
        from haystack.inputs import Raw
        from haystack.query import SearchQuerySet, SQ  # noqa

        sqs = None

        # Retrieve Query Params

        # Text search
        query = parameters.get('q', None)

        # Types and subtypes to filter (map, layer, vector, etc)
        type_facets = parameters.getlist("type__in", [])

        # If coming from explore page, add type filter from resource_name
        resource_filter = self._meta.resource_name.rstrip("s")
        if resource_filter != "base" and resource_filter not in type_facets:
            type_facets.append(resource_filter)

        # Publication date range (start,end)
        date_end = parameters.get("date__lte", None)
        date_start = parameters.get("date__gte", None)

        # Topic category filter
        category = parameters.getlist("category__identifier__in")

        # Keyword filter
        keywords = parameters.getlist("keywords__slug__in")

        # Region filter
        regions = parameters.getlist("regions__name__in")

        # Owner filters
        owner = parameters.getlist("owner__username__in")

        # Sort order
        sort = parameters.get("order_by", "relevance")

        # Geospatial Elements
        bbox = parameters.get("extent", None)

        # Filter by Type and subtype
        if type_facets is not None:
            types = []
            subtypes = []

            for type in type_facets:
                if type in ["map", "layer", "document", "user"]:
                    # Type is one of our Major Types (not a sub type)
                    types.append(type)
                elif type in LAYER_SUBTYPES.keys():
                    subtypes.append(type)

            if len(subtypes) > 0:
                types.append("layer")
                sqs = SearchQuerySet().narrow("subtype:%s" %
                                              ','.join(map(str, subtypes)))

            if len(types) > 0:
                sqs = (SearchQuerySet() if sqs is None else sqs).narrow(
                    "type:%s" % ','.join(map(str, types)))

        # Filter by Query Params
        # haystack bug? if boosted fields aren't included in the
        # query, then the score won't be affected by the boost
        if query:
            if query.startswith('"') or query.startswith('\''):
                # Match exact phrase
                phrase = query.replace('"', '')
                sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                    SQ(title__exact=phrase) |
                    SQ(description__exact=phrase) |
                    SQ(content__exact=phrase)
                )
            else:
                words = [
                    w for w in re.split(
                        '\W',
                        query,
                        flags=re.UNICODE) if w]
                for i, search_word in enumerate(words):
                    if i == 0:
                        sqs = (SearchQuerySet() if sqs is None else sqs) \
                            .filter(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )
                    elif search_word in ["AND", "OR"]:
                        pass
                    elif words[i - 1] == "OR":  # previous word OR this word
                        sqs = sqs.filter_or(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )
                    else:  # previous word AND this word
                        sqs = sqs.filter(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )

        # filter by category
        if category:
            sqs = (SearchQuerySet() if sqs is None else sqs).narrow(
                'category:%s' % ','.join(map(str, category)))

        # filter by keyword: use filter_or with keywords_exact
        # not using exact leads to fuzzy matching and too many results
        # using narrow with exact leads to zero results if multiple keywords
        # selected
        if keywords:
            for keyword in keywords:
                sqs = (
                    SearchQuerySet() if sqs is None else sqs).filter_or(
                    keywords_exact=keyword)

        # filter by regions: use filter_or with regions_exact
        # not using exact leads to fuzzy matching and too many results
        # using narrow with exact leads to zero results if multiple keywords
        # selected
        if regions:
            for region in regions:
                sqs = (
                    SearchQuerySet() if sqs is None else sqs).filter_or(
                    regions_exact__exact=region)

        # filter by owner
        if owner:
            sqs = (
                SearchQuerySet() if sqs is None else sqs).narrow(
                    "owner__username:%s" % ','.join(map(str, owner)))

        # filter by date
        if date_start:
            sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                SQ(date__gte=date_start)
            )

        if date_end:
            sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                SQ(date__lte=date_end)
            )

        # Filter by geographic bounding box
        if bbox:
            left, bottom, right, top = bbox.split(',')
            sqs = (
                SearchQuerySet() if sqs is None else sqs).exclude(
                SQ(
                    bbox_top__lte=bottom) | SQ(
                    bbox_bottom__gte=top) | SQ(
                    bbox_left__gte=right) | SQ(
                        bbox_right__lte=left))

        # Apply sort
        if sort.lower() == "-date":
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("-date")
        elif sort.lower() == "date":
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("date")
        elif sort.lower() == "title":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "title_sortable")
        elif sort.lower() == "-title":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "-title_sortable")
        elif sort.lower() == "-popular_count":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "-popular_count")
        else:
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("-date")

        return sqs

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Get the list of objects that matches the filter
        sqs = self.build_haystack_filters(request.GET)

        if not settings.SKIP_PERMS_FILTER:

            filter_set = get_objects_for_user(
                request.user, 'base.view_resourcebase')

            filter_set = get_visible_resources(
                filter_set,
                request.user if request else None,
                admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
                unpublished_not_visible=settings.RESOURCE_PUBLISHING,
                private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

            filter_set_ids = filter_set.values_list('id')
            # Do the query using the filterset and the query term. Facet the
            # results
            if len(filter_set) > 0:
                sqs = sqs.filter(id__in=filter_set_ids).facet('type').facet('subtype').facet(
                    'owner') .facet('keywords').facet('regions').facet('category')
            else:
                sqs = None
        else:
            sqs = sqs.facet('type').facet('subtype').facet(
                'owner').facet('keywords').facet('regions').facet('category')

        if sqs:
            # Build the Facet dict
            facets = {}
            for facet in sqs.facet_counts()['fields']:
                facets[facet] = {}
                for item in sqs.facet_counts()['fields'][facet]:
                    facets[facet][item[0]] = item[1]

            # Paginate the results
            paginator = Paginator(sqs, request.GET.get('limit'))

            try:
                page = paginator.page(
                    int(request.GET.get('offset') or 0) /
                    int(request.GET.get('limit'), 0) + 1)
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")

            if page.has_previous():
                previous_page = page.previous_page_number()
            else:
                previous_page = 1
            if page.has_next():
                next_page = page.next_page_number()
            else:
                next_page = 1
            total_count = sqs.count()
            objects = page.object_list
        else:
            next_page = 0
            previous_page = 0
            total_count = 0
            facets = {}
            objects = []

        object_list = {
            "meta": {
                "limit": settings.CLIENT_RESULTS_LIMIT,
                "next": next_page,
                "offset": int(getattr(request.GET, 'offset', 0)),
                "previous": previous_page,
                "total_count": total_count,
                "facets": facets,
            },
            "objects": map(lambda x: self.get_haystack_api_fields(x), objects),
        }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def get_haystack_api_fields(self, haystack_object):
        object_fields = dict(
            (k, v) for k, v in haystack_object.get_stored_fields().items() if not re.search(
                '_exact$|_sortable$', k))
        return object_fields

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
        objects = self.obj_get_list(
            bundle=base_bundle,
            **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(
            request.GET,
            sorted_objects,
            resource_uri=self.get_resource_uri(),
            limit=self._meta.limit,
            max_limit=self._meta.max_limit,
            collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        to_be_serialized = self.alter_list_data_to_serialize(
            request,
            to_be_serialized)

        return self.create_response(
            request, to_be_serialized, response_objects=objects)

    def format_objects(self, objects):
        """
        Format the objects for output in a response.
        """
        if 'has_time' in self.VALUES:
            idx = self.VALUES.index('has_time')
            del self.VALUES[idx]
        objects_json = objects.values(*self.VALUES)

        # hack needed because dehydrate does not seem to work in CommonModelApi
        for item in objects_json:
            if item['thumbnail_url'] and len(item['thumbnail_url']) == 0:
                item['thumbnail_url'] = staticfiles.static(settings.MISSING_THUMBNAIL)
            if item['title'] and len(item['title']) == 0:
                item['title'] = 'No title'
            if 'owner__username' in item:
                username = item['owner__username']
                profiles = Profile.objects.filter(username=username)
                if profiles:
                    full_name = (profiles[0].get_full_name() or username)
                    item['owner_name'] = full_name
        return objects_json

    def create_response(
            self,
            request,
            data,
            response_class=HttpResponse,
            response_objects=None,
            **response_kwargs):
        """
        Extracts the common "which-format/serialize/return-response" cycle.

        Mostly a useful shortcut/hook.
        """

        # If an user does not have at least view permissions, he won't be able
        # to see the resource at all.
        filtered_objects_ids = None
        if response_objects:
            filtered_objects_ids = [
                item.id for item in response_objects if request.user.has_perm(
                    'view_resourcebase', item.get_self_resource())]

        if isinstance(
                data,
                dict) and 'objects' in data and not isinstance(
                data['objects'],
                list):
            if filtered_objects_ids:
                data['objects'] = [
                    x for x in list(
                        self.format_objects(
                            data['objects'])) if x['id'] in filtered_objects_ids]
            else:
                data['objects'] = list(self.format_objects(data['objects']))

            # give geonode version
            data['geonode_version'] = get_version()

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)

        return response_class(
            content=serialized,
            content_type=build_content_type(desired_format),
            **response_kwargs)

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


class ResourceBaseResource(CommonModelApi):

    """ResourceBase api"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.polymorphic_queryset() \
            .distinct().order_by('-date')
        resource_name = 'base'
        excludes = ['csw_anytext', 'metadata_xml']
        authentication = MultiAuthentication(SessionAuthentication(), GeonodeApiKeyAuthentication())


class FeaturedResourceBaseResource(CommonModelApi):

    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.filter(featured=True).order_by('-date')
        resource_name = 'featured'
        authentication = MultiAuthentication(SessionAuthentication(), GeonodeApiKeyAuthentication())


class LayerResource(CommonModelApi):

    """Layer API"""
    links = fields.ListField(
        attribute='links',
        null=True,
        use_in='detail',
        default=[])
    if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
        default_style = fields.ForeignKey(
            'geonode.api.api.StyleResource',
            attribute='qgis_default_style',
            null=True)
        styles = fields.ManyToManyField(
            'geonode.api.api.StyleResource',
            attribute='qgis_styles',
            null=True,
            use_in='detail')
    elif check_ogc_backend(geoserver.BACKEND_PACKAGE):
        default_style = fields.ForeignKey(
            'geonode.api.api.StyleResource',
            attribute='default_style',
            null=True)
        styles = fields.ManyToManyField(
            'geonode.api.api.StyleResource',
            attribute='styles',
            null=True,
            use_in='detail')

    def format_objects(self, objects):
        """
        Formats the object then adds a geogig_link as necessary.
        """
        formatted_objects = []
        for obj in objects:
            # convert the object to a dict using the standard values.
            # includes other values
            values = self.VALUES + [
                'alternate',
                'name'
            ]
            formatted_obj = model_to_dict(obj, fields=values)
            username = obj.owner.get_username()
            full_name = (obj.owner.get_full_name() or username)
            formatted_obj['owner__username'] = username
            formatted_obj['owner_name'] = full_name
            if obj.category:
                formatted_obj['category__gn_description'] = obj.category.gn_description
            if obj.group:
                formatted_obj['group'] = obj.group
                try:
                    formatted_obj['group_name'] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj['group_name'] = obj.group

            formatted_obj['keywords'] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj['regions'] = [r.name for r in obj.regions.all()] if obj.regions else []

            # add the geogig link
            formatted_obj['geogig_link'] = obj.geogig_link

            # provide style information
            bundle = self.build_bundle(obj=obj)
            formatted_obj['default_style'] = self.default_style.dehydrate(
                bundle, for_list=True)

            if self.links.use_in == 'all' or self.links.use_in == 'list':
                formatted_obj['links'] = self.dehydrate_links(
                    bundle)
            # Add resource uri
            formatted_obj['resource_uri'] = self.get_resource_uri(bundle)

            # Probe Remote Services
            formatted_obj['store_type'] = 'dataset'
            formatted_obj['online'] = True
            if hasattr(obj, 'storeType'):
                formatted_obj['store_type'] = obj.storeType
                if obj.storeType == 'remoteStore' and hasattr(obj, 'remote_service'):
                    formatted_obj['online'] = (obj.remote_service.probe == 200)

            # put the object on the response stack
            formatted_objects.append(formatted_obj)
        return formatted_objects

    def dehydrate_links(self, bundle):
        """Dehydrate links field."""

        dehydrated = []
        obj = bundle.obj
        link_fields = [
            'extension',
            'link_type',
            'name',
            'mime',
            'url'
        ]
        for l in obj.link_set.all():
            formatted_link = model_to_dict(l, fields=link_fields)
            dehydrated.append(formatted_link)

        return dehydrated

    def populate_object(self, obj):
        """Populate results with necessary fields

        :param obj: Layer obj
        :type obj: Layer
        :return:
        """
        if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            # Provides custom links for QGIS Server styles info
            # Default style
            try:
                obj.qgis_default_style = obj.qgis_layer.default_style
            except:
                obj.qgis_default_style = None

            # Styles
            try:
                obj.qgis_styles = obj.qgis_layer.styles
            except:
                obj.qgis_styles = []
        return obj

    def build_bundle(
            self, obj=None, data=None, request=None, **kwargs):
        """Override build_bundle method to add additional info."""

        if obj is None and self._meta.object_class:
            obj = self._meta.object_class()

        elif obj:
            obj = self.populate_object(obj)

        return Bundle(
            obj=obj,
            data=data,
            request=request, **kwargs)

    def patch_detail(self, request, **kwargs):
        """Allow patch request to update default_style.

        Request body must match this:

        {
            'default_style': <resource_uri_to_style>
        }

        """
        reason = 'Can only patch "default_style" field.'
        try:
            body = json.loads(request.body)
            if 'default_style' not in body:
                return http.HttpBadRequest(reason=reason)
            match = resolve(body['default_style'])
            style_id = match.kwargs['id']
            api_name = match.kwargs['api_name']
            resource_name = match.kwargs['resource_name']
            if not (resource_name == 'styles' and api_name == 'api'):
                raise Exception()

            from geonode.qgis_server.models import QGISServerStyle

            style = QGISServerStyle.objects.get(id=style_id)

            layer_id = kwargs['id']
            layer = Layer.objects.get(id=layer_id)
        except:
            return http.HttpBadRequest(reason=reason)

        from geonode.qgis_server.views import default_qml_style

        request.method = 'POST'
        response = default_qml_style(
            request,
            layername=layer.name,
            style_name=style.name)

        if isinstance(response, TemplateResponse):
            if response.status_code == 200:
                return HttpResponse(status=200)

        return self.error_response(request, response.content)

    # copy parent attribute before modifying
    VALUES = CommonModelApi.VALUES[:]
    VALUES.append('typename')

    class Meta(CommonMetaApi):
        queryset = Layer.objects.distinct().order_by('-date')
        resource_name = 'layers'
        detail_uri_name = 'id'
        include_resource_uri = True
        allowed_methods = ['get', 'patch']
        excludes = ['csw_anytext', 'metadata_xml']
        authentication = MultiAuthentication(SessionAuthentication(), GeonodeApiKeyAuthentication())
        filtering = CommonMetaApi.filtering
        # Allow filtering using ID
        filtering.update({
            'id': ALL,
            'name': ALL,
            'alternate': ALL,
        })


class MapResource(CommonModelApi):

    """Maps API"""

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
            full_name = (obj.owner.get_full_name() or username)
            formatted_obj['owner__username'] = username
            formatted_obj['owner_name'] = full_name
            if obj.category:
                formatted_obj['category__gn_description'] = obj.category.gn_description
            if obj.group:
                formatted_obj['group'] = obj.group
                try:
                    formatted_obj['group_name'] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj['group_name'] = obj.group

            formatted_obj['keywords'] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj['regions'] = [r.name for r in obj.regions.all()] if obj.regions else []

            # Probe Remote Services
            formatted_obj['store_type'] = 'map'
            formatted_obj['online'] = True

            # get map layers
            map_layers = obj.layers
            formatted_layers = []
            map_layer_fields = [
                'id'
                'stack_order',
                'format',
                'name',
                'opacity',
                'group',
                'visibility',
                'transparent',
                'ows_url',
                'layer_params',
                'source_params',
                'local'
            ]
            for layer in map_layers:
                formatted_map_layer = model_to_dict(
                     layer, fields=map_layer_fields)
                formatted_layers.append(formatted_map_layer)
            formatted_obj['layers'] = formatted_layers
            formatted_objects.append(formatted_obj)
        return formatted_objects

    class Meta(CommonMetaApi):
        queryset = Map.objects.distinct().order_by('-date')
        resource_name = 'maps'
        authentication = MultiAuthentication(SessionAuthentication(), GeonodeApiKeyAuthentication())


class DocumentResource(CommonModelApi):

    """Documents API"""

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
            full_name = (obj.owner.get_full_name() or username)
            formatted_obj['owner__username'] = username
            formatted_obj['owner_name'] = full_name
            if obj.category:
                formatted_obj['category__gn_description'] = obj.category.gn_description
            if obj.group:
                formatted_obj['group'] = obj.group
                try:
                    formatted_obj['group_name'] = GroupProfile.objects.get(slug=obj.group.name)
                except GroupProfile.DoesNotExist:
                    formatted_obj['group_name'] = obj.group

            formatted_obj['keywords'] = [k.name for k in obj.keywords.all()] if obj.keywords else []
            formatted_obj['regions'] = [r.name for r in obj.regions.all()] if obj.regions else []

            # Probe Remote Services
            formatted_obj['store_type'] = 'dataset'
            formatted_obj['online'] = True

            formatted_objects.append(formatted_obj)
        return formatted_objects

    class Meta(CommonMetaApi):
        filtering = CommonMetaApi.filtering
        filtering.update({'doc_type': ALL})
        queryset = Document.objects.distinct().order_by('-date')
        resource_name = 'documents'
        authentication = MultiAuthentication(SessionAuthentication(), GeonodeApiKeyAuthentication())
