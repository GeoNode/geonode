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

from geonode.maps.views import default_map_config
from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile 
from geonode.search.search import combined_search_results
from geonode.search.util import resolve_extension
from geonode.search.normalizers import apply_normalizers
from geonode.search.query import query_from_request
from geonode.search.query import BadQuery

from taggit.models import Tag

from datetime import datetime
from time import time
from itertools import chain
import json
import cPickle as pickle
import operator
import logging
import zlib

logger = logging.getLogger(__name__)

_extra_context = resolve_extension('extra_context')

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10


def _create_viewer_config():
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
    _map = Map(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)
    return json.dumps(_map.viewer_json(*DEFAULT_BASE_LAYERS))
_viewer_config = _create_viewer_config()


def search_page(request, template='search/search.html', **kw): 
    results, query = search_api(request, format='html', **kw)
    facets = results.pop('facets')
    chained = chain()
    for key in results.keys():
        chained = chain(chained, results[key])
    results = list(chained)
    total = 0
    for val in facets.values(): total+=val
    total -= facets['raster'] + facets['vector']
    return render_to_response(template, RequestContext(request, {'object_list': results, 'total': total, 
        'facets': facets, 'query': json.dumps(query.get_query_response()), 'tags': Tag.objects.all()}))

def advanced_search(request, **kw):
    params = {}
    if kw:
        params.update(kw)

    context = _get_search_context()
    context['init_search'] = json.dumps(params)
    return render_to_response('search/advanced_search.html', RequestContext(request, context))

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
        'users' : Profile.objects.count()
    }
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
    cache.set(cache_key, context, 60)

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
    if request.method not in ('GET','POST'):
        return HttpResponse(status=405)
    debug = logger.isEnabledFor(logging.DEBUG)
    if debug:
        connection.queries = []
    ts = time()
    try:
        query = query_from_request(request, kwargs)
        if format == 'html':
            items = _search_natural(query)
        else:
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
            return items, query
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

def _search_natural(query):
    # to support super fast paging results, cache the intermediates
    results = None
    cache_time = 60
    if query.cache:
        key = query.cache_key()
        results = cache.get(key)
        if results:
            # put it back again - this basically extends the lease
            cache.add(key, results, cache_time)

    if not results:
        results = combined_search_results(query)
        if query.cache:
            dumped = zlib.compress(pickle.dumps((results)))
            logger.debug("cached search results %s", len(dumped))
            cache.set(key, dumped, cache_time)

    else:
        results = pickle.loads(zlib.decompress(results))

    return results

def _search(query):
    # to support super fast paging results, cache the intermediates
    results = None
    cache_time = 60
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