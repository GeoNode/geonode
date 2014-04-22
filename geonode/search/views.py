#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.cache import cache
from taggit.models import TaggedItem

if "geonode.contrib.groups" in settings.INSTALLED_APPS:
    from geonode.contrib.groups.models import Group
from geonode.maps.views import default_map_config
from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile 
from geonode.search.search import combined_search_results
from geonode.search.util import resolve_extension
from geonode.search.normalizers import apply_normalizers, MapNormalizer, LayerNormalizer, DocumentNormalizer, OwnerNormalizer, GroupNormalizer
from geonode.search.query import query_from_request
from geonode.search.query import BadQuery
from geonode.base.models import TopicCategory

from datetime import datetime
from time import time
import json
import cPickle as pickle
import operator
import logging
import zlib

import xmlrpclib

logger = logging.getLogger(__name__)

_extra_context = resolve_extension('extra_context')

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10


def _create_viewer_config():
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
    _map = Map(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)
    return json.dumps(_map.viewer_json(*DEFAULT_BASE_LAYERS))
_viewer_config = _create_viewer_config()


def search_page(request, template='search/search.html', **kw):
    initial_query = request.REQUEST.get('q','')

    if getattr(settings, 'HAYSTACK_SEARCH', False) and "haystack" in settings.INSTALLED_APPS:
        query = query_from_request(request, kw)
        search_response, results = haystack_search_api(request, format="html", **kw)
        facets = search_response['facets']

        categories = {}
        counts = search_response["categories"]
        topics = TopicCategory.objects.all()
        for topic in topics:
            if topic.identifier in counts:
                categories[topic] = counts[topic.identifier]
            else:
                categories[topic] = 0

        total = search_response['total']

        tags = {}

        # get the keywords and their count
        keywords = search_response["keywords"]
        for keyword in keywords:
            try:
                tagged_item = TaggedItem.objects.filter(tag__name=keyword)[0]
                tags[tagged_item.tag.slug] = tags.get(tagged_item.tag.slug,{})
                tags[tagged_item.tag.slug]['slug'] = tagged_item.tag.name
                tags[tagged_item.tag.slug]['name'] = tagged_item.tag.name
                tags[tagged_item.tag.slug]['count'] = keywords[keyword]
            except Exception, e:
                logger.error("Could not find TaggedItem for keyword %s" % keyword)

    else:
        results, facets, query = search_api(request, format='html', **kw)
        categories = {}
        tags = {}

        # get the keywords and their count
        for item in results:
            for tagged_item in item.o.tagged_items.all():
                tags[tagged_item.tag.slug] = tags.get(tagged_item.tag.slug,{})
                tags[tagged_item.tag.slug]['slug'] = tagged_item.tag.slug
                tags[tagged_item.tag.slug]['name'] = tagged_item.tag.name
                tags[tagged_item.tag.slug]['count'] = tags[tagged_item.tag.slug].get('count',0) + 1

        total = 0
        for val in facets.values(): total+=val
        total -= facets['raster'] + facets['vector']

    return render_to_response(template, RequestContext(request, {'object_list': results, 'total': total, "categories": categories,
                                                                 'facets': facets, 'query': json.dumps(query.get_query_response()), 'tags': tags,
                                                                 'initial_query': initial_query}))

def advanced_search(request, **kw):
    ctx = {
        'category_list': TopicCategory.objects.all(),
    }
    
    return render_to_response('search/advanced_search.html', RequestContext(request, ctx))

def _get_search_context():
    cache_key = 'simple_search_context'
    context = cache.get(cache_key)
    if context: return context

    counts = {
        'maps' : Map.objects.count(),
        'layers' : Layer.objects.count(),
        'vector' : Layer.objects.filter(storeType='dataStore').count(),
        'raster' : Layer.objects.filter(storeType='coverageStore').count(),
        'documents': Document.objects.count(),
        'users' : Profile.objects.count(),
    }
    if "geonode.contrib.groups" in settings.INSTALLED_APPS:
        counts['groups'] = Group.objects.count()

    topics = Layer.objects.all().values_list('topic_category',flat=True)
    topic_cnts = {}
    for t in topics: topic_cnts[t] = topic_cnts.get(t,0) + 1
    context = {
        'viewer_config': _viewer_config,
        "site" : settings.SITEURL,
        'counts' : counts,
        'users' : User.objects.all(),
        'topics' : topic_cnts,
        'keywords' : _get_all_keywords()
    }
    if _extra_context:
        _extra_context(context)
    cache.set(cache_key, context, settings.CACHE_TIME)

    return context


def _get_all_keywords():
    allkw = {}
    # @todo tagging added to maps and contacts, depending upon search type,
    # need to get these... for now it doesn't matter (in mapstory) as
    # only layers support keywords ATM.
    for l in Layer.objects.all().select_related().only('keywords'):
        kw = [ k.name for k in l.keywords.all() ]
        for k in kw:
            allkw[k] = allkw.get(k,0) + 1

    return allkw


def search_api(request, format='json', **kwargs):
    if settings.HAYSTACK_SEARCH and "haystack" in settings.INSTALLED_APPS:
        return haystack_search_api(request, format=format, **kwargs)

    if request.method not in ('GET','POST'):
        return HttpResponse(status=405)
    debug = logger.isEnabledFor(logging.DEBUG)
    if debug:
        connection.queries = []
    ts = time()
    try:
        query = query_from_request(request, kwargs)
        items, facets = _search(query)
        ts1 = time() - ts
        if debug:
            ts = time()
        if format != 'html':
            results = _search_json(query, items, facets, ts1)
            if debug:
                ts2 = time() - ts
                logger.debug('generated combined search results in %s, %s',ts1,ts2)
                logger.debug('with %s db queries',len(connection.queries))
        if format == 'html':
            return items, facets, query
        else:
            return results

    except Exception, ex:
        if not isinstance(ex, BadQuery):
            logger.exception("error during search")
            raise ex
        return HttpResponse(json.dumps({
            'success' : False,
            'errors' : [str(ex)]
        }), status=400)

def _search_json(query, items, facets, time):
    total = len(items)

    if query.limit is not None and query.limit > 0:
        items = items[query.start:query.start + query.limit]

    # unique item id for ext store (this could be done client side)
    iid = query.start
    for r in items:
        r.iid = iid
        iid += 1

    exclude = query.params.get('exclude')
    exclude = set(exclude.split(',')) if exclude else ()
    items = map(lambda r: r.as_dict(exclude), items)

    results = {
        '_time' : time,
        'results' : items,
        'total' :  total,
        'success' : True,
        'query' : query.get_query_response(),
        'facets' : facets
    }
    return HttpResponse(json.dumps(results), mimetype="application/json")


def cache_key(query,filters):
    return str(reduce(operator.xor,map(hash,filters.items())) ^ hash(query))

def _search(query):
    # to support super fast paging results, cache the intermediates
    results = None
    cache_time = settings.CACHE_TIME 
    if query.cache:
        key = query.cache_key()
        results = cache.get(key)
        if results:
            # put it back again - this basically extends the lease
            cache.add(key, results, cache_time)

    if not results:
        results = combined_search_results(query)
        facets = results['facets']
        results = apply_normalizers(results)
        if query.cache:
            dumped = zlib.compress(pickle.dumps((results, facets)))
            logger.debug("cached search results %s", len(dumped))
            cache.set(key, dumped, cache_time)

    else:
        results, facets = pickle.loads(zlib.decompress(results))

    # @todo - sorting should be done in the backend as it can optimize if
    # the query is restricted to one model. has implications for caching...
    if query.sort != None:
        if query.sort == 'title':
            keyfunc = lambda r: r.title().lower()
        elif query.sort == 'last_modified':
            old = datetime(1,1,1)
            keyfunc = lambda r: r.last_modified() or old
        else:
            keyfunc = lambda r: getattr(r, query.sort)()

        results.sort(key=keyfunc, reverse=not query.order)

    return results, facets


def author_list(req):
    q = User.objects.all()

    query = req.REQUEST.get('query',None)
    start = int(req.REQUEST.get('start',0))
    limit = int(req.REQUEST.get('limit',20))

    if query:
        q = q.filter(username__icontains=query)

    vals = q.values_list('username',flat=True)[start:start+limit]
    results = {
        'total' : q.count(),
        'names' : [ dict(name=v) for v in vals ]
    }
    return HttpResponse(json.dumps(results), mimetype="application/json")

def haystack_search_api(request, format="json", **kwargs):
    """
    View that drives the search api
    """
    from haystack.inputs import Raw
    from haystack.query import SearchQuerySet, SQ

    # Retrieve Query Params
    id = request.REQUEST.get("id", None)
    query = request.REQUEST.get('q',None)
    category = request.REQUEST.get("category", None)
    limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20)))
    startIndex = int(request.REQUEST.get("startIndex", 0))
    sort = request.REQUEST.get("sort", "relevance")
    type_facets = request.REQUEST.get("type", None)
    format = request.REQUEST.get("format", format)
    date_start = request.REQUEST.get("start_date", None)
    date_end = request.REQUEST.get("end_date", None)
    keyword = request.REQUEST.get("kw", None)
    service = request.REQUEST.get("service", None)
    local = request.REQUEST.get("local", None)


    # Geospatial Elements
    bbox = request.REQUEST.get("extent", None)

    ts = time()
    sqs = SearchQuerySet()

    limit = min(limit,500)

    # Filter by ID
    if id:
        sqs = sqs.narrow("django_id:%s" % id)



    # Filter by Type and subtype
    if type_facets is not None:
        type_facets = type_facets.replace("owner","user").split(",")
        subtype_facets = ["vector", "raster"]
        types = []
        subtypes = []
        for type in type_facets:
            if type in ["map", "layer", "user", "document", "group"]:
                # Type is one of our Major Types (not a sub type)
                types.append(type)
            elif type in subtype_facets:
                subtypes.append(type)

        if len(subtypes) > 0:
            for sub_type in subtype_facets:
                if sub_type not in subtypes:
                    sqs = sqs.exclude(subtype='%s' % sub_type)

        if len(types) > 0:
            sqs = sqs.narrow("type:%s" % ','.join(map(str, types)))

    # Filter by Query Params
    # haystack bug? if boosted fields aren't included in the
    # query, then the score won't be affected by the boost
    if query:
        if query.startswith('"') or query.startswith('\''):
            #Match exact phrase
            phrase = query.replace('"','')
            sqs = sqs.filter(
                SQ(title__exact=phrase) |
                SQ(abstract__exact=phrase) |
                SQ(content__exact=phrase)
            )
        else:
            words = query.split()
            for word in range(0,len(words)):
                if word == 0:
                    sqs = sqs.filter(
                        SQ(title=Raw(words[word])) |
                        SQ(abstract=Raw(words[word])) |
                        SQ(content=Raw(words[word]))
                    )
                elif words[word] in ["AND","OR"]:
                    pass
                elif words[word-1] == "OR": #previous word OR this word
                    sqs = sqs.filter_or(
                        SQ(title=Raw(words[word])) |
                        SQ(abstract=Raw(words[word])) |
                        SQ(content=Raw(words[word]))
                    )
                else: #previous word AND this word
                    sqs = sqs.filter(
                        SQ(title=Raw(words[word])) |
                        SQ(abstract=Raw(words[word])) |
                        SQ(content=Raw(words[word]))
                    )

    # filter by cateory
    if category:
        sqs = sqs.narrow('category:%s' % category)

    #filter by keyword
    if keyword:
        sqs = sqs.narrow('keywords:%s' % keyword)

    if date_start:
        sqs = sqs.filter(
            SQ(date__gte=date_start)
        )

    if date_end:
        sqs = sqs.filter(
            SQ(date__lte=date_end)
        )

    """
    ### Code to filter on temporal extent start/end dates instead

    if date_start or date_end:
        #Exclude results with no dates at all
        sqs = sqs.filter(
            SQ(temporal_extent_start=Raw("[* TO *]")) | SQ(temporal_extent_end=Raw("[* TO *]"))
        )
    if temporal_start and temporal_end:
        #Return anything with a start date < date_end or an end date > date_start
        sqs = sqs.filter(
            SQ(temporal_extent_end__gte=date_start) | SQ(temporal_extent_start__lte=date_end)
        )
    elif temporal_start:
        #Exclude anything with an end date <date_start
        sqs = sqs.exclude(
            SQ(temporal_extent_end__lte=date_start)
        )
    elif temporal_end:
        #Exclude anything with a start date > date_end
        sqs = sqs.exclude(
            SQ(temporal_extent_start__gte=date_end)
        )
    """

    if bbox:
        left,right,bottom,top = bbox.split(',')
        sqs = sqs.filter(
            # first check if the bbox has at least one point inside the window
            SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) & SQ(bbox_top__gte=bottom) & SQ(bbox_top__lte=top) | #check top_left is inside the window
            SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) & SQ(bbox_top__lte=top) &  SQ(bbox_top__gte=bottom) | #check top_right is inside the window
            SQ(bbox_bottom__gte=bottom) & SQ(bbox_bottom__lte=top) & SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) | #check bottom_right is inside the window
            SQ(bbox_top__lte=top) & SQ(bbox_top__gte=bottom) & SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) | #check bottom_left is inside the window
            # then check if the bbox is including the window
            SQ(bbox_left__lte=left) & SQ(bbox_right__gte=right) & SQ(bbox_bottom__lte=bottom) & SQ(bbox_top__gte=top)
        )


    # Filter by permissions
    '''
    ### Takes too long with many results.
    ### Instead, show all results but disable links on restricted ones.

    for i, result in enumerate(sqs):
        if result.type == 'layer':
            if not request.user.has_perm('layers.view_layer',obj = result.object):
                sqs = sqs.exclude(id = result.id)
        if result.type == 'map':
            if not request.user.has_perm('maps.view_map',obj = result.object):
                sqs = sqs.exclude(id = result.id)
    '''

    #filter by service
    '''
    if service:
        sqs = sqs.narrow('service:%s' % service)

    if local:
        sqs = sqs.narrow('local:%s' % local)
    '''

    # Apply Sort
    # TODO: Handle for Revised sort types
    # [relevance, alphabetically, rating, created, updated, popularity]
    if sort.lower() == "newest":
        sqs = sqs.order_by("-modified")
    elif sort.lower() == "oldest":
        sqs = sqs.order_by("modified")
    elif sort.lower() == "alphaaz":
        sqs = sqs.order_by("title_sortable")
    elif sort.lower() == "alphaza":
        sqs = sqs.order_by("-title_sortable")
    elif sort.lower() == "popularity":
        sqs = sqs.order_by("-popular_count")
    else:
        sqs = sqs.order_by("-_score")


    # Setup Search Results
    results = []
    items = []

    # Build the result based on the limit
    for i, result in enumerate(sqs[startIndex:startIndex + limit]):
        logger.info(result)
        data = result.get_stored_fields()
        resource = None
        if "modified" in data:
            data["modified"] = data["modified"].strftime("%Y-%m-%dT%H:%M:%S.%f")
        if "temporal_extent_start" in data and data["temporal_extent_start"] is not None:
            data["temporal_extent_start"] = data["temporal_extent_start"].strftime("%Y-%m-%dT%H:%M:%S.%f")
        if "temporal_extent_end" in data and data["temporal_extent_end"] is not None:
            data["temporal_extent_end"] = data["temporal_extent_end"].strftime("%Y-%m-%dT%H:%M:%S.%f")
        if data['type'] == "map":
            resource = MapNormalizer(Map.objects.get(pk=data['oid']))
        elif data['type'] == "layer":
            resource = LayerNormalizer(Layer.objects.get(pk=data['oid']))
        elif data['type'] == "user":
            resource = OwnerNormalizer(Profile.objects.get(pk=data['oid']))
        elif data['type'] == "document":
            resource = DocumentNormalizer(Document.objects.get(pk=data['oid']))
        elif data['type'] == "group" and "geonode.contrib.groups" in settings.INSTALLED_APPS:
            resource = GroupNormalizer(Group.objects.get(pk=data['oid']))
        if resource:
            resource.rating = data["rating"] if "rating" in data else 0
        results.append(data)
        items.append(resource)


    # Setup Facet Counts
    sqs = sqs.facet("type").facet("subtype")

    sqs = sqs.facet('category')

    sqs = sqs.facet('keywords')

    sqs = sqs.facet('service')

    sqs = sqs.facet('local')

    facet_counts = sqs.facet_counts()

    # Prepare Search Results
    data = {
        "success": True,
        "total": sqs.count(),
        "query_info": {
            "q": query,
            "startIndex": startIndex,
            "limit": limit,
            "sort": sort,
            "type": type_facets,
            },
        "results": results,
        "facets": dict(facet_counts.get("fields")['type']+facet_counts.get('fields')['subtype']) if sqs.count() > 0 else [],
        "categories": {facet[0]:facet[1] for facet in facet_counts.get('fields')['category']} if sqs.count() > 0 else {},
        "keywords": {facet[0]:facet[1] for facet in facet_counts.get('fields')['keywords']} if sqs.count() > 0 else {},
    }

    # Return Results
    ts1 = time() - ts

    if format == "html": #Send to search/explore page
        return data, items
    elif format == "raw":
        return HttpResponse(json.dumps(data), mimetype="application/json")
    else:
        query = query_from_request(request, kwargs)
        return _search_json(query, items, data["facets"], ts1)
