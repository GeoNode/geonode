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

from django.db import backend
from django.db.models import Q
from django.contrib.auth.models import User

from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.maps.models import MapLayer
from geonode.people.models import Contact

from geonode.silage import extension
from geonode.silage.models import filter_by_period
from geonode.silage.models import filter_by_extent
from geonode.silage.models import using_geodjango

import operator


def _rank_rules(model, *rules):
    # prefix field names with model's db table to avoid ambiguity
    for r in rules:
        r[0] = '"%s"."%s"' % (model._meta.db_table, r[0])
    return rules


def _filter_results(l):
    '''If the layer name doesn't match any of the patterns, it shows in the results'''
    return not any(p.search(l['name']) for p in extension.exclude_regex)


def _add_relevance(q, query, rank_rules):
    # for unittests, it doesn't make sense to test this as it's postgres
    # specific SQL - instead test/verify directly using a query and getting SQL
    if 'sqlite' in backend.__name__: return q
    
    eq = """CASE WHEN %s = '%s' THEN %s ELSE 0 END"""
    frag = """CASE WHEN position(lower('%s') in lower(%s)) >= 1 THEN %s ELSE 0 END"""
    
    preds = []

    preds.extend( [ eq % (r[0],query.query,r[1]) for r in rank_rules] )
    preds.extend( [ frag % (query.query,r[0],r[2]) for r in rank_rules] )
    
    words = query.split_query
    if len(words) > 1:
        for w in words:
            preds.extend( [ frag % (w,r[0],r[2] / 2) for r in rank_rules] )
            
    sql = " + ".join(preds)
            
    # ugh - work around bug
    q = q.defer(None)
    return q.extra(select={'relevance':sql})


def _build_kw_query(query, query_keywords=False):
    '''Build an OR query on title and abstract from provided search text.
    if query_keywords is provided, include a query on the keywords attribute
    
    return a Q object
    '''
    subquery = [
        Q(title__icontains=kw) | Q(abstract__icontains=kw) for kw in query.split_query
    ]
    if query_keywords:
        subquery.append(_build_kw_only_query(query.split_query))
    return reduce( operator.or_, subquery)


def _build_kw_only_query(keywords):
    return reduce(operator.or_, [Q(keywords__name__contains=kw) for kw in keywords])


def _get_owner_results(query):
    # make sure all contacts have a user attached
    q = extension.owner_query(query)
    
    if q is None: return None
    
    if query.kw:
        # hard to handle - not supporting at the moment
        return
    
    if query.owner:
        q = q.filter(user__username__icontains = query.owner)
    
    if query.extent:
        q = filter_by_extent(Map, q, query.extent, True) | \
            filter_by_extent(Layer, q, query.extent, True)
    
    if query.period:
        q = filter_by_period(Map, q, *query.period, user=True) | \
            filter_by_period(Layer, q, *query.period, user=True)
    
    if query.added:
        q = q.filter(user__date_joined__gt = query.added)
    
    if query.query:
        qs = Q(user__username__icontains=query.query) | \
             Q(user__first_name__icontains=query.query) | \
             Q(user__last_name__icontains=query.query)
        for field in extension.owner_query_fields:
            qs = qs | Q(**{'%s__icontains' % field: query.query})
        q = q.filter(qs)
        
        rules = _rank_rules(User,['username', 10, 5]) + \
                _rank_rules(Contact,['organization', 5, 2])
        added = extension.owner_rank_rules()
        if added:
            rules = rules + _rank_rules(*added)
        q = _add_relevance(q, query, rules)
    return q


def _get_map_results(query):
    q = extension.map_query(query)
    
    if query.query:
        q = q.filter(title__icontains=query.query) | \
            q.filter(abstract__icontains=query.query) | \
            q.filter(_build_kw_query(query, query_keywords=True))

    if query.owner:
        q = q.filter(owner__username=query.owner)

    if query.extent:
        q = filter_by_extent(Map, q, query.extent)
        
    if query.added:
        q = q.filter(last_modified__gte=query.added)
    
    if query.period:
        q = filter_by_period(Map, q, *query.period)
        
    if query.kw:
        # this is a somewhat nested query but it performs way faster
        layers_with_kw = Layer.objects.filter(_build_kw_only_query(query.kw)).values('typename')
        map_layers_with = MapLayer.objects.filter(name__in=layers_with_kw).values('map')
        q = q.filter(id__in=map_layers_with)
    if query.query:
        rules = _rank_rules(Map,
            ['title',10, 5],
            ['abstract',5, 2],
        )
        q = _add_relevance(q, query, rules)

    return q.distinct()

    
def _get_layer_results(query):
    
    q = extension.layer_query(query)
    if extension.exclude_patterns:
        name_filter = reduce(operator.or_,[ Q(name__regex=f) for f in extension.exclude_patterns])
        q = q.exclude(name_filter)
    if query.query:
        q = q.filter(_build_kw_query(query, query_keywords=True)) | \
            q.filter(name__icontains = query.query) | \
            q.filter(title__icontains=query.query)
    # we can optimize kw search here
    # maps will still be slow, but this way all the layers are filtered
    # bybw before the cruddy in-memory filter
    if query.kw:
        q = q.filter(_build_kw_only_query(query.kw))
            
    if query.owner:
        q = q.filter(owner__username=query.owner)
            
    if query.type and query.type != 'layer':
        q = q.filter(storeType = query.type)
        
    if query.extent:
        q = filter_by_extent(Layer, q, query.extent)
        
    if query.added:
        q = q.filter(date__gte=query.added)
        
    if query.period:
        q = filter_by_period(Layer, q, *query.period)
       
    # this is a special optimization for prefetching results when requesting
    # all records via search
    # keywords and thumbnails cannot be prefetched at the moment due to
    # the way the contenttypes are implemented
    if query.limit == 0 and using_geodjango:
        q = q.defer(None).prefetch_related("owner","spatial_temporal_index")
    
    if query.query:
        rules = _rank_rules(Layer,
            ['name',10, 1],
            ['title',10, 5],
            ['abstract',5, 2],
        )
        q = _add_relevance(q, query, rules)

    return q.distinct()
                

def combined_search_results(query):
    results = {}
    
    bytype = query.type
    
    if bytype is None or bytype == u'map':
        results['maps'] = _get_map_results(query)
        
    if bytype is None or bytype == u'layer':
        results['layers'] = _get_layer_results(query)
        
    if bytype is None or bytype == u'owner':
        results['owners'] = _get_owner_results(query)
        
    return results
