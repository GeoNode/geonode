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

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.cache import cache

from geonode.maps.views import default_map_config
from geonode.maps.models import Contact
from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.silage.search import combined_search_results
from geonode.silage.util import resolve_extension

import json
import cPickle as pickle
import operator
import logging
import zlib

logger = logging.getLogger(__name__)

_SEARCH_PARAMS = ['bytype','bykw','byowner','byextent','byadded','byperiod','exclude','cache']

# settings API
_search_config = getattr(settings,'SIMPLE_SEARCH_SETTINGS', {})
_SEARCH_PARAMS.extend(_search_config.get('extra_query',[]))
_extra_context = resolve_extension('extra_context')
# end settings API

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10

def _create_viewer_config():
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(None)
    _map = Map(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)
    return json.dumps(_map.viewer_json(added_layers=DEFAULT_BASE_LAYERS, authenticated=False))
_viewer_config = _create_viewer_config()

def new_search_page(request, **kw):
    
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)
    
    if kw:
        params = dict(params)
        params.update(kw)

    context = _get_search_context()
    context['init_search'] = json.dumps(params or {})
     
    return render_to_response('silage/search.html', RequestContext(request, context))
    
def _get_search_context():
    cache_key = 'simple_search_context'
    context = cache.get(cache_key)
    if context: return context
    
    counts = {
        'maps' : Map.objects.count(),
        'layers' : Layer.objects.count(),
        'vector' : Layer.objects.filter(storeType='dataStore').count(),
        'raster' : Layer.objects.filter(storeType='coverageStore').count(),
        'users' : Contact.objects.count()
    }
    topics = Layer.objects.all().values_list('topic_category',flat=True)
    topic_cnts = {}
    for t in topics: topic_cnts[t] = topic_cnts.get(t,0) + 1
    context = {
        'viewer_config': _viewer_config,
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
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
    if settings.USE_GEONETWORK:
        allkw = Layer.objects.gn_catalog.get_all_keywords()
    else:    
        allkw = {}
        # @todo tagging added to maps and contacts, depending upon search type,
        # need to get these... for now it doesn't matter (in mapstory) as
        # only layers support keywords ATM.
        for l in Layer.objects.all().select_related().only('keywords'):
            kw = [ k.name for k in l.keywords.all() ]
            for k in kw:
                allkw[k] = allkw.get(k,0) + 1

    return allkw

def new_search_api(request):
    from time import time
#    from django.db import connection
#    connection.queries = []
    ts = time()
    try:
        params = _search_params(request)
        start = params[1]
        total, items = _new_search(*params)
        ts1 = time() - ts
        ts = time()
        results = _search_json(params[-1], items, total, start, ts1)
        ts2 = time() - ts
        logger.info('generated combined search results in %s, %s',ts1,ts2)
#        print ts1,ts2, connection.queries.__len__()
        return results
    except Exception, ex:
        logger.exception("error during search")
        return HttpResponse(json.dumps({
            'success' : False,
            'errors' : [str(ex)]
        }), status=400)

def new_search_api_reduced(request):
    from time import time

    ts = time()
    params = _search_params(request)
    total, items = _new_search(*params)
    ts = time() - ts
    logger.info('generated combined search results in %s',ts)
    idfun = lambda o: (isinstance(o, Map) and 'm%s' or 'l%s') % o.o.pk
    results = {
        "_time" : ts,
        "rows" : [ idfun(i) for i in items ],
        "total" : total
    }
    return HttpResponse(json.dumps(results), mimetype="application/json")

def _search_params(request):
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
        # compat
        if 'startIndex' in params:
            start = int(params.get('startIndex',0))
    except:
        start = 0
    try:
        limit = int(params.get('limit', DEFAULT_MAPS_SEARCH_BATCH_SIZE))
    except:
        limit = DEFAULT_MAPS_SEARCH_BATCH_SIZE
        
    # handle old search link parameters
    if 'sort' in params and 'dir' in params:
        sort_field = params['sort']
        sort_asc = params['dir'] == 'ASC'
    else:    
        sort_field, sort_asc = {
            'newest' : ('last_modified',False),
            'oldest' : ('last_modified',True),
            'alphaaz' : ('title',True),
            'alphaza' : ('title',False),
            'popularity' : ('rank',False),
            'rel' : ('relevance',False)

        }[params.get('sort','newest')]

    filters = dict([(k,params.get(k,None) or None) for k in _SEARCH_PARAMS])
    
    # stuff the user in there, too, if authenticated
    filters['user'] = request.user if request.user.is_authenticated() else None
    
    filters['limit'] = limit
    
    # compat
    aliases = dict(type='bytype',bbox='byextent')
    for k,v in aliases.items():
        if k in params: filters[v] = params[k]
                
    if filters.get('byperiod'):
        filters['byperiod'] = tuple(filters['byperiod'].split(','))

    return query, start, limit, sort_field, sort_asc, filters
    
    
def _search_json(params, results, total, start, time):
    # unique item id for ext store (this could be done client side)
    iid = start
    for r in results:
        r.iid = iid
        iid += 1
    
    exclude = params.get('exclude')
    exclude = set(exclude.split(',')) if exclude else ()
    results = map(lambda r: r.as_dict(exclude),results)
        
    results = {
        '_time' : time,
        'rows' : results,
        'total' :  total,
        'success' : True,
    }
    return HttpResponse(json.dumps(results), mimetype="application/json")


def cache_key(query,filters):
    return str(reduce(operator.xor,map(hash,filters.items())) ^ hash(query))


def _new_search(query, start, limit, sort_field, sort_asc, filters):
    # to support super fast paging results, cache the intermediates
    use_cache = filters.get('cache',1)
    results = None
    cache_time = 60
    if use_cache:
        key = cache_key(query,filters)
        results = cache.get(key)
        if results:
            # put it back again - this basically extends the lease
            cache.add(key, results, cache_time)
        
    if not results:
        results = combined_search_results(query,filters)
        if use_cache:
            dumped = zlib.compress(pickle.dumps(results))
            logger.info("cached search results %s" % len(dumped))
            cache.set(key, dumped, cache_time)

    else:
        results = pickle.loads(zlib.decompress(results))

    filter_fun = []
    # careful when creating lambda or function filters inline like this
    # as multiple filters cannot use the same local variable or they
    # will overwrite each other
    
    # this is a cruddy, in-memory search since there is no database relationship
    if settings.USE_GEONETWORK:
        kw = filters['bykw']
        if kw:
            filter_fun.append(lambda r: 'keywords' in r.as_dict(()) and kw in r.as_dict(())['keywords'])
    
    for fun in filter_fun:
        results = filter(fun,results)

    # default sort order by id (could be last_modified when external layers are dealt with)
    if sort_field == 'title':
        keyfunc = lambda r: r.title().lower()
    else:
        keyfunc = lambda r: getattr(r,sort_field)()
    results.sort(key=keyfunc,reverse=not sort_asc)
    
    if limit > 0:
        results = results[start:start+limit]
    
    return len(results), results


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
    