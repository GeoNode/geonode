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

import re

from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings


#@jahangir091
from django.shortcuts import get_object_or_404
from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.timesince import timesince
from django.utils.translation import ugettext as _
#end


from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils import trailing_slash
from actstream.models import Action
from guardian.shortcuts import get_objects_for_user

from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from tastypie.utils.mime import build_content_type

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase
from geonode.base.models import HierarchicalKeyword
from .authorization import GeoNodeAuthorization

#@jahangir091
from geonode.api.api import MetaFavorite
from geonode.base.models import FavoriteResource
from geonode.groups.models import GroupProfile
from geonode.social.templatetags.social_tags import get_data
#end

from .api import TagResource, RegionResource, OwnersResource
from .api import ThesaurusKeywordResource
from .api import TopicCategoryResource
from .api import FILTER_TYPES

if settings.HAYSTACK_SEARCH:
    from haystack.query import SearchQuerySet  # noqa

LAYER_SUBTYPES = {
    'vector': 'dataStore',
    'raster': 'coverageStore',
    'remote': 'remoteStore',
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
                 'owner': ALL_WITH_RELATIONS,
                 'date': ALL,
                 'resource_type':ALL,

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
    owner = fields.ToOneField(OwnersResource, 'owner', full=True)
    tkeywords = fields.ToManyField(ThesaurusKeywordResource, 'tkeywords', null=True)
    VALUES = [
        # fields in the db
        'id',
        'uuid',
        'title',
        'date',
        'abstract',
        'csw_wkt_geometry',
        'csw_type',
        'owner__username',
        'share_count',
        'popular_count',
        'srid',
        'category__gn_description',
        'supplemental_information',
        'thumbnail_url',
        'detail_url',
        'rating',
        'bbox_x0',
        'bbox_x1',
        'bbox_y0',
        'bbox_y1'
    ]

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(CommonModelApi, self).build_filters(filters)
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
                    if filtered:
                        filtered = filtered | semi_filtered.filter(
                            Layer___storeType=LAYER_SUBTYPES[the_type])
                    else:
                        filtered = semi_filtered.filter(
                            Layer___storeType=LAYER_SUBTYPES[the_type])
                else:
                    if filtered:
                        filtered = filtered | semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
                    else:
                        filtered = semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
        else:
            filtered = semi_filtered

        if extent:
            filtered = self.filter_bbox(filtered, extent)

        if keywords:
            filtered = self.filter_h_keywords(filtered, keywords)

        return filtered

    def filter_h_keywords(self, queryset, keywords):
        filtered = queryset
        treeqs = HierarchicalKeyword.objects.none()
        for keyword in keywords:
            try:
                kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
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
            # Get the list of objects the user has access to
            filter_set = get_objects_for_user(request.user, 'base.view_resourcebase')
            if settings.RESOURCE_PUBLISHING:
                filter_set = filter_set.filter(is_published=True)

            filter_set_ids = filter_set.values_list('id')
            # Do the query using the filterset and the query term. Facet the
            # results
            if len(filter_set) > 0:
                sqs = sqs.filter(id__in=filter_set_ids).facet('type').facet('subtype').facet('owner')\
                    .facet('keywords').facet('regions').facet('category')
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
                    int(request.GET.get('offset')) /
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
                "limit": settings.API_LIMIT_PER_PAGE,
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
        object_fields = dict((k, v) for k, v in haystack_object.get_stored_fields().items()
                             if not re.search('_exact$|_sortable$', k))
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

        return self.create_response(request, to_be_serialized, response_objects=objects)

    def format_objects(self, objects):
        """
        Format the objects for output in a response.
        """
        return objects.values(*self.VALUES)

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


	#@jahangir091
        VALUES = [
            # fields in the db
            'id',
            'uuid',
            'title',
            'date',
            'abstract',
            'csw_wkt_geometry',
            'csw_type',
            'owner__username',
            'share_count',
            'popular_count',
            'srid',
            'category__gn_description',
            'supplemental_information',
            'thumbnail_url',
            'detail_url',
            'rating',
            'featured',
            'resource_type'
        ]
	#end


        # If an user does not have at least view permissions, he won't be able to see the resource at all.
        filtered_objects_ids = None
        if response_objects:
            filtered_objects_ids = [item.id for item in response_objects if
                                    request.user.has_perm('view_resourcebase', item.get_self_resource())]
        if isinstance(
                data,
                dict) and 'objects' in data and not isinstance(
                data['objects'],
                list):
            if filtered_objects_ids:
                data['objects'] = [x for x in list(self.format_objects(data['objects']))
                                   if x['id'] in filtered_objects_ids]
            else:
                data['objects'] = list(self.format_objects(data['objects']))

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
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'base'
        excludes = ['csw_anytext', 'metadata_xml']


class FeaturedResourceBaseResource(CommonModelApi):

    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.filter(featured=True).order_by('-date')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'featured'


class LayerResource(CommonModelApi):

    """Layer API"""

    class Meta(CommonMetaApi):
        queryset = Layer.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'layers'
        excludes = ['csw_anytext', 'metadata_xml']

    #jahangir091
    def get_object_list(self, request):
        group_id = request.GET.get('group', None)
        if group_id:
            group = get_object_or_404(GroupProfile, id=group_id)
            return super(LayerResource, self).get_object_list(request).filter(group=group)
        else:
            return super(LayerResource, self).get_object_list(request).filter(status='ACTIVE')
    #end

class MapResource(CommonModelApi):

    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'maps'


class DocumentResource(CommonModelApi):

    """Maps API"""

    class Meta(CommonMetaApi):
        filtering = CommonMetaApi.filtering
        filtering.update({'doc_type': ALL})
        queryset = Document.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'documents'



#@jahangir091
class CommonFavorite(ModelResource):
    def dehydrate(self, bundle):

        if bundle.request.user.is_authenticated():
            try:
                bundle.data['favorite'] = FavoriteResource.objects.get(user=bundle.request.user, resource=ResourceBase.objects.get(id=bundle.obj.id)).active
            except FavoriteResource.DoesNotExist:
                bundle.data['favorite'] = False
        bundle.data['owner__username'] = bundle.obj.owner.username
        bundle.data['category'] = bundle.obj.category
        bundle.data['group'] = bundle.obj.group
        if bundle.request.user in bundle.obj.group.get_managers():
            bundle.data['can_make_featured'] = True
        else:
            bundle.data['can_make_featured'] = False

        return bundle


class LayerResourceWithFavorite(CommonFavorite):

    """Layer API with Favorite"""

    class Meta(MetaFavorite):
        queryset = Layer.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'layers_with_favorite'
        excludes = ['csw_anytext', 'metadata_xml']
        filtering = {
            'group': ALL,
            'featured': ALL
        }
    def get_object_list(self, request):
        group = request.GET.get('group')
        if group:
            return super(LayerResourceWithFavorite, self).get_object_list(request).filter(group=group)
        else:
            return super(LayerResourceWithFavorite, self).get_object_list(request).filter(status='ACTIVE')


class MapResourceWithFavorite(CommonFavorite):

    """Maps API with Favorite"""

    class Meta(MetaFavorite):
        queryset = Map.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'maps_with_favorite'
        filtering = {
            'id': ALL
        }


class DocumentResourceWithFavorite(CommonFavorite):

    """Maps API with Favorite"""

    class Meta(MetaFavorite):
        queryset = Document.objects.distinct().order_by('-date').filter(status='ACTIVE')
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'documents_with_favorite'


class GroupsResourceWithFavorite(ModelResource):

    """Grpups API with Favorite"""

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
        resource_name = 'groups_with_favorite'
        ordering = ['title', 'date']

    def dehydrate(self, bundle):

        if bundle.request.user.is_authenticated():
            try:
                bundle.data['favorite'] = FavoriteResource.objects.get(user=bundle.request.user, group=GroupProfile.objects.get(id=bundle.obj.id)).active
            except FavoriteResource.DoesNotExist:
                bundle.data['favorite'] = False
        return bundle


class GroupActivity(ModelResource):
    """
    This API return Activities for a specific group.
    it takes three parameters.
    limit = limit of queryset. used for pagination.
    group = slug for a specific group and the api will return
        activities for that group.
    option = layers, maps, comments. the option for activity.
        if layers is given then it will return layer activity
        if maps is given thenn it will return maps activity
        if comments is given it will return comments activity
        if no options is given then it will return all the activity of that group
    if no group slug is given then the API will return empty queryset
    if the requested user is not authenticated, it will return empty queryset.
    """
    class Meta:
        queryset = Action.objects.filter(public=True)
        resource_name = 'group_activity'

    def get_object_list(self, request):
        if request.user.is_authenticated():
            contenttypes = ContentType.objects.all()
            for ct in contenttypes:
                if ct.name == 'layer':
                    ct_layer_id = ct.id
                if ct.name == 'map':
                    ct_map_id = ct.id
                if ct.name == 'comment':
                    ct_comment_id = ct.id
            group_slug = request.GET.get('group')
            option = request.GET.get('option')
            if group_slug:
                group = get_object_or_404(GroupProfile, slug=group_slug)
                members = ([(member.user.id) for member in group.member_queryset()])
                if option == 'comments':
                    return Action.objects.filter(public=True, actor_object_id__in=members, action_object_content_type__id=ct_comment_id)
                elif option == 'maps':
                    return Action.objects.filter(public=True, actor_object_id__in=members, action_object_content_type__id=ct_map_id)
                elif option == 'layers':
                    return Action.objects.filter(public=True, actor_object_id__in=members, action_object_content_type__id=ct_layer_id)
                else:
                    return Action.objects.filter(public=True, actor_object_id__in=members)
            else:
                return Action.objects.filter(public=True)[:0]
        else:
            return Action.objects.filter(public=True)[:0]

    def dehydrate(self, bundle):
        actor = bundle.obj.actor
        activity_class = 'activity'
        verb = bundle.obj.verb
        username = bundle.obj.actor.username
        target = bundle.obj.target
        object_type = None
        object = bundle.obj.action_object
        raw_action = get_data(bundle.obj, 'raw_action')
        object_name = get_data(bundle.obj, 'object_name')
        preposition = _("to")
        fragment = None
        thumbnail_url = None
        object_url = None

        if object:
            object_type = object.__class__._meta.object_name.lower()

        if target:
            target_type = target.__class__._meta.object_name.lower()  # noqa

        if actor is None:
            return str()

    # Set the item's class based on the object.
        if object:
            if object_type == 'comment':
                activity_class = 'comment'
                preposition = _("on")
                object = None
                fragment = "comments"

            if object_type == 'map':
                activity_class = 'map'

            if object_type == 'layer':
                activity_class = 'layer'

        if raw_action == 'deleted':
            activity_class = 'delete'

        if raw_action == 'created' and object_type == 'layer':
            activity_class = 'upload'

        bundle.data['activity_class'] = activity_class,
        bundle.data['action'] = bundle.obj,
        bundle.data['actor'] = actor,
        bundle.data['object'] = object,
        bundle.data['object_name'] = object_name,
        bundle.data['preposition'] = preposition,
        bundle.data['target'] = target,
        bundle.data['timestamp'] = bundle.obj.timestamp,
        bundle.data['username'] = username,
        bundle.data['verb'] = verb,
        bundle.data['fragment'] = fragment
        if object:
            bundle.data['object_thumbnail_url'] = object.thumbnail_url
            bundle.data['object_absolute_url'] = object.get_absolute_url()
        bundle.data['actor_absolute_url'] = bundle.obj.actor.get_absolute_url()
        bundle.data['object_name'] = object_name
        if fragment:
            bundle.data['target_absolute_url'] = target.get_absolute_url()
        bundle.data['timesince'] = timesince(bundle.obj.timestamp)

        return bundle


class WorkSpaceLayerApi(ModelResource):
    """
    This API is a Big one.
    It returns all the required data to show member and admin workspaces.
    it takes three parameters as below:
    user_type = type of user. 'member' or 'admin'
    resource_state = state of resource according to member or user.
        options for this field are:
        admin ('user_approval_request_list', 'approved_list', 'user_draft_list', 'denied_list')
        member('draft_list', 'pending_list', 'denied_list', 'active_list')
    """
    def dehydrate_date_created(self, bundle):
        return bundle.obj.date_created.strftime('%b %d %Y  %H:%M:%S ')

    def dehydrate_date_updated(self, bundle):
        return bundle.obj.date_updated.strftime('%b %d %Y  %H:%M:%S ')

    class Meta:
        queryset = Layer.objects.all()
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'workspace_layer_api'
        excludes = ['csw_anytext', 'metadata_xml']

    def get_object_list(self, request):
        nothing = Layer.objects.all()[:0]
        if request.user.is_authenticated():
            user_type = request.GET.get('user_type')
            resource_state = request.GET.get('resource_state')
            resource_type = 'layer'
            user = request.user

            if user_type == 'admin':
                if user.is_manager_of_any_group:
                    groups = GroupProfile.objects.filter(groupmember__user=user, groupmember__role='manager')
                    if resource_type == 'layer':
                        if resource_state == 'user_approval_request_list':
                            return Layer.objects.filter(status='PENDING', group__in=groups).order_by('date_updated')
                        elif resource_state == 'approved_list':
                            return Layer.objects.filter(status='ACTIVE', group__in=groups).order_by('date_updated')
                        elif resource_state == 'user_draft_list':
                            return Layer.objects.filter(status='DRAFT', group__in=groups).order_by('date_updated')
                        elif resource_state == 'denied_list':
                            return Layer.objects.filter(status='DENIED', group__in=groups).order_by('date_updated')
                        else:
                            return nothing
                else:
                    return nothing

            elif user_type == 'member':
                if resource_type == 'layer':
                    if resource_state == 'draft_list':
                        return Layer.objects.filter(owner=user, status='DRAFT').order_by('date_updated')
                    elif resource_state == 'pending_list':
                        return Layer.objects.filter(owner=user, status='PENDING').order_by('date_updated')
                    elif resource_state == 'denied_list':
                        return Layer.objects.filter(owner=user, status='DENIED').order_by('date_updated')
                    elif resource_state == 'active_list':
                        return Layer.objects.filter(owner=user, status='ACTIVE').order_by('date_updated')
                    else:
                        return nothing
                else:
                        return nothing

        else:
            return nothing

    def dehydrate(self, bundle):
        bundle.data['group'] = bundle.obj.group
        bundle.data['current_iteration'] = bundle.obj.current_iteration
        bundle.data['time'] = bundle.obj.date_updated.ctime()
        bundle.data['owner'] = bundle.obj.owner.username
        bundle.data['last_auditor'] = bundle.obj.last_auditor
        return bundle



class WorkSpaceDocumentApi(ModelResource):
    """
    This API is a Big one.
    It returns all the required data to show member and admin workspaces.
    it takes three parameters as below:
    user_type = type of user. 'member' or 'admin'
    resource_state = state of resource according to member or user.
        options for this field are:
        admin ('user_approval_request_list', 'approved_list', 'user_draft_list', 'denied_list')
        member('draft_list', 'pending_list', 'denied_list', 'active_list')
    """

    def dehydrate_date_created(self, bundle):
        return bundle.obj.date_created.strftime('%b %d %Y  %H:%M:%S ')

    def dehydrate_date_updated(self, bundle):
        return bundle.obj.date_updated.strftime('%b %d %Y  %H:%M:%S ')

    class Meta:
        queryset = Document.objects.all()
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'workspace_document_api'

    def get_object_list(self, request):
        nothing = Document.objects.all()[:0]
        if request.user.is_authenticated():
            user_type = request.GET.get('user_type')
            resource_state = request.GET.get('resource_state')
            resource_type = 'document'
            user = request.user

            if user_type == 'admin':
                if user.is_manager_of_any_group:
                    groups = GroupProfile.objects.filter(groupmember__user=user, groupmember__role='manager')

                    if resource_type == 'document':
                        if resource_state == 'user_approval_request_list':
                            return Document.objects.filter(status='PENDING', group__in=groups).order_by('date_updated')
                        elif resource_state == 'approved_list':
                            return Document.objects.filter(status='ACTIVE', group__in=groups).order_by('date_updated')
                        elif resource_state == 'user_draft_list':
                            return Document.objects.filter(status='DRAFT', group__in=groups).order_by('date_updated')
                        elif resource_state == 'denied_list':
                            return Document.objects.filter(status='DENIED', group__in=groups).order_by('date_updated')
                        else:
                            return nothing
                    else:
                        return nothing

                else:
                    return nothing

            elif user_type == 'member':

                if resource_type == 'document':
                    if resource_state == 'draft_list':
                        return Document.objects.filter(owner=user, status='DRAFT').order_by('date_updated')
                    elif resource_state == 'pending_list':
                        return Document.objects.filter(owner=user, status='PENDING').order_by('date_updated')
                    elif resource_state == 'denied_list':
                        return Document.objects.filter(owner=user, status='DENIED').order_by('date_updated')
                    elif resource_state == 'active_list':
                        return Document.objects.filter(owner=user, status='ACTIVE').order_by('date_updated')
                    else:
                        return nothing
                else:
                    return nothing

        else:
            return nothing


    def dehydrate(self, bundle):
        bundle.data['group'] = bundle.obj.group
        bundle.data['current_iteration'] = bundle.obj.current_iteration
        bundle.data['time'] = bundle.obj.date_updated.ctime()
        bundle.data['owner'] = bundle.obj.owner.username
        bundle.data['last_auditor'] = bundle.obj.last_auditor
        return bundle


class WorkSpaceMapApi(ModelResource):
    """
    This API is a Big one.
    It returns all the required data to show member and admin workspaces.
    it takes three parameters as below:
    user_type = type of user. 'member' or 'admin'
    resource_state = state of resource according to member or user.
        options for this field are:
        admin ('user_approval_request_list', 'approved_list', 'user_draft_list', 'denied_list')
        member('draft_list', 'pending_list', 'denied_list', 'active_list')
    """

    def dehydrate_date_created(self, bundle):
        return bundle.obj.date_created.strftime('%b %d %Y  %H:%M:%S ')

    def dehydrate_date_updated(self, bundle):
        return bundle.obj.date_updated.strftime('%b %d %Y  %H:%M:%S ')

    class Meta:
        queryset = Map.objects.all()
        if settings.RESOURCE_PUBLISHING:
            queryset = queryset.filter(is_published=True)
        resource_name = 'workspace_map_api'

    def get_object_list(self, request):
        nothing = Map.objects.all()[:0]
        if request.user.is_authenticated():
            user_type = request.GET.get('user_type')
            resource_state = request.GET.get('resource_state')
            resource_type = 'map'
            user = request.user

            if user_type == 'admin':
                if user.is_manager_of_any_group:
                    groups = GroupProfile.objects.filter(groupmember__user=user, groupmember__role='manager')
                    if resource_type == 'map':
                        if resource_state == 'user_approval_request_list':
                            return Map.objects.filter(status='PENDING', group__in=groups).order_by('date_updated')
                        elif resource_state == 'approved_list':
                            return Map.objects.filter(status='ACTIVE', group__in=groups).order_by('date_updated')
                        elif resource_state == 'user_draft_list':
                            return Map.objects.filter(status='DRAFT', group__in=groups).order_by('date_updated')
                        elif resource_state == 'denied_list':
                            return Map.objects.filter(status='DENIED', group__in=groups).order_by('date_updated')
                        else:
                            return nothing
                    else:
                        return nothing

                else:
                    return nothing

            elif user_type == 'member':
                if resource_type == 'map':
                    if resource_state == 'draft_list':
                        return Map.objects.filter(owner=user, status='DRAFT').order_by('date_updated')
                    elif resource_state == 'pending_list':
                        return Map.objects.filter(owner=user, status='PENDING').order_by('date_updated')
                    elif resource_state == 'denied_list':
                        return Map.objects.filter(owner=user, status='DENIED').order_by('date_updated')
                    elif resource_state == 'active_list':
                        return Map.objects.filter(owner=user, status='ACTIVE').order_by('date_updated')
                    else:
                        return nothing
                else:
                    return nothing

        else:
            return nothing


    def dehydrate(self, bundle):
        bundle.data['group'] = bundle.obj.group
        bundle.data['current_iteration'] = bundle.obj.current_iteration
        bundle.data['time'] = bundle.obj.date_updated.ctime()
        bundle.data['owner'] = bundle.obj.owner.username
        bundle.data['last_auditor'] = bundle.obj.last_auditor
        return bundle

#end