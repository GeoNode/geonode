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

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template import defaultfilters
from django.contrib.gis.gdal import Envelope
from django.contrib.auth.models import User

from geonode.maps.models import Contact
from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.maps.models import MapLayer
from geonode.maps.views import _metadata_search
from geonode.maps.views import _split_query

from geonode.silage.util import resolve_extension
from geonode.silage.models import LayerIndex
from geonode.silage.models import MapIndex
from geonode.silage.models import filter_by_period

from avatar.util import get_default_avatar_url

import re
import operator
from datetime import date
from datetime import timedelta

_date_fmt = lambda dt: dt.strftime('%b %d %Y')
_USER_DISPLAY = 'User'
_MAP_DISPLAY = 'Map'
_LAYER_DISPLAY = 'Layer'

# settings API
_search_config = getattr(settings,'SIMPLE_SEARCH_SETTINGS', {})

_exclude_patterns = _search_config.get('layer_exclusions',[])

_exclude_regex = [ re.compile(e) for e in _exclude_patterns ]

_process_results = resolve_extension('process_search_results')
if _process_results is None:
    _process_results = lambda r: r
    
_owner_query = resolve_extension('owner_query')
if not _owner_query:
    _owner_query = lambda q,k: Contact.objects.filter()
    
_owner_query_fields = resolve_extension('owner_query_fields') or []
    
_layer_query = resolve_extension('layer_query')
if not _layer_query:
    _layer_query = lambda q,k: Layer.objects.filter()
    
_map_query = resolve_extension('map_query')
if not _map_query:
    _map_query = lambda q,k: Map.objects.filter()

_display_names = resolve_extension('display_names')
if _display_names:
    _USER_DISPLAY = _display_names.get('user')
    _MAP_DISPLAY = _display_names.get('map')
    _LAYER_DISPLAY = _display_names.get('layer')
    
_owner_rank_rules = resolve_extension('owner_rank_rules')
if not _owner_rank_rules:
    _owner_rank_rules = lambda: []

# end settings API

def _rank_rules(model, *rules):
    # prefix field names with model's db table to avoid ambiguity
    for r in rules:
        r[0] = '"%s"."%s"' % (model._meta.db_table, r[0])
    return rules


def _filter_results(l):
    '''If the layer name doesn't match any of the patterns, it shows in the results'''
    return not any(p.search(l['name']) for p in _exclude_regex)

def _bbox(obj):
    idx = None
    # the one-to-one reverse relationship requires special handling if null :(
    # maybe one day: https://code.djangoproject.com/ticket/10227
    try:
        idx = obj.spatial_temporal_index
    except ObjectDoesNotExist:
        pass
    # unknown extent, just give something that works
    extent = idx.extent.extent if idx else (-180,-90,180,90)
    return dict(minx=extent[0], miny=extent[1], maxx=extent[2], maxy=extent[3])

class Normalizer:
    '''Base class to allow lazy normalization of Map and Layer attributes.
    
    The fields we support sorting on are rank, title, last_modified.
    Instead of storing these (to keep pickle query size small), expose via methods.
    '''
    def __init__(self,o,data = None):
        self.o = o
        self.data = data
        self.dict = None
    def rank(self):
        return (self.rating + 1) * (self.views + 1)
    def title(self):
        return self.o.title
    def last_modified(self):
        raise Exception('abstract')
    def relevance(self):
        return getattr(self.o, 'relevance', 0)
    def as_dict(self, exclude):
        if self.dict is None:
            if self.o._deferred:
                self.o = getattr(type(self.o),'objects').get(pk = self.o.pk)
            self.dict = self.populate(self.data or {}, exclude)
            self.dict['iid'] = self.iid
            self.dict['rating'] = self.rating
            self.dict['relevance'] = getattr(self.o, 'relevance', 0)
            if hasattr(self,'views'):
                self.dict['views'] = self.views
        if exclude:
            for e in exclude:
                if e in self.dict: self.dict.pop(e)
        return self.dict
    
    
class MapNormalizer(Normalizer):
    def last_modified(self):
        return self.o.last_modified
    def populate(self, doc, exclude):
        map = self.o
        # resolve any local layers and their keywords
        # @todo this makes this search awful slow and these should be lazily evaluated
        local_kw = [ l.keyword_list() for l in map.local_layers if l.keywords]
        keywords = local_kw and list(set( reduce(lambda a,b: a+b, local_kw))) or []
        doc['id'] = map.id
        doc['title'] = map.title
        doc['abstract'] = defaultfilters.linebreaks(map.abstract)
        doc['topic'] = '', # @todo
        doc['detail'] = reverse('geonode.maps.views.map_controller', args=(map.id,))
        doc['owner'] = map.owner.username
        doc['owner_detail'] = reverse('about_storyteller', args=(map.owner.username,))
        doc['last_modified'] = _date_fmt(map.last_modified)
        doc['_type'] = 'map'
        doc['_display_type'] = _MAP_DISPLAY
        doc['thumb'] = map.get_thumbnail_url()
        doc['keywords'] = keywords
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(map)
        return doc
        
class LayerNormalizer(Normalizer):
    def last_modified(self):
        return self.o.date
    def populate(self, doc, exclude):
        layer = self.o
        doc['owner'] = layer.owner.username
        doc['thumb'] = layer.get_thumbnail_url()
        doc['last_modified'] = _date_fmt(layer.date)
        doc['id'] = layer.id
        doc['_type'] = 'layer'
        doc['owsUrl'] = layer.get_virtual_wms_url()
        doc['topic'] = layer.topic_category
        doc['name'] = layer.typename
        doc['abstract'] = defaultfilters.linebreaks(layer.abstract)
        doc['storeType'] = layer.storeType
        doc['_display_type'] = _LAYER_DISPLAY
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(layer)
        if not settings.USE_GEONETWORK:
            doc['keywords'] = layer.keyword_list()
            doc['title'] = layer.title
            doc['detail'] = layer.get_absolute_url()
        #if 'download_links' not in exclude:
        #    links = layer.download_links()
        #    for i,e in enumerate(links):
        #        links[i] = [ unicode(l) for l in e]
        #    doc['download_links'] = links
        owner = layer.owner
        if owner:
            doc['owner_detail'] = reverse('about_storyteller', args=(layer.owner.username,))
        return doc


_default_avatar_url = get_default_avatar_url()
class OwnerNormalizer(Normalizer):
    def title(self):
        return self.o.user.username
    def last_modified(self):
        return self.o.user.date_joined
    def populate(self, doc, exclude):
        contact = self.o
        user = contact.user
        try:
            doc['thumb'] = user.avatar_set.all()[0].avatar_url(80)
        except IndexError:
            doc['thumb'] = _default_avatar_url
        doc['id'] = user.username
        doc['title'] = user.get_full_name() or user.username
        doc['organization'] = contact.organization
        doc['abstract'] = contact.blurb
        doc['last_modified'] = _date_fmt(self.last_modified())
        doc['detail'] = reverse('about_storyteller', args=(user.username,))
        doc['layer_cnt'] = Layer.objects.filter(owner = user).count()
        doc['map_cnt'] = Map.objects.filter(owner = user).count()
        doc['_type'] = 'owner'
        doc['_display_type'] = _USER_DISPLAY
        return doc
    
def _get_owner_results(results, query, kw):
    # make sure all contacts have a user attached
    q = _owner_query(query, kw)
    
    if q is None: return None
    
    if kw['bykw']:
        # hard to handle - not supporting at the moment
        return
    
    byowner = kw.get('byowner')
    if byowner:
        q = q.filter(user__username__icontains = byowner)
    
    byextent = kw.get('byextent')
    if byextent:
        q = _filter_by_extent(MapIndex, q, byextent, True) | \
            _filter_by_extent(LayerIndex, q, byextent, True)
    
    byperiod = kw.get('byperiod')
    if byperiod:
        q = _filter_by_period(MapIndex, q, byperiod, True) | \
            _filter_by_period(LayerIndex, q, byperiod, True)
    
    byadded = parse_by_added(kw.get('byadded'))
    if byadded:
        q = q.filter(user__date_joined__gt = byadded)
    
    if query:
        qs = Q(user__username__icontains=query) | \
             Q(user__first_name__icontains=query) | \
             Q(user__last_name__icontains=query)
        for field in _owner_query_fields:
            qs = qs | Q(**{'%s__icontains' % field: query})
        q = q.filter(qs)
        
        rules = _rank_rules(User,['username', 10, 5]) + \
                _rank_rules(Contact,['organization', 5, 2])
        added = _owner_rank_rules()
        if added:
            rules = rules + _rank_rules(*added)
        q = _add_relevance(q, query, rules)
    
    results.extend( _process_results(map(OwnerNormalizer,q)))
        
def _get_map_results(results, query, kw):
    q = _map_query(query,kw)
        
    byowner = kw.get('byowner')
    if byowner:
        q = q.filter(owner__username=byowner)

    if query:
        q = q.filter(_build_kw_query(query))
        
    byextent = kw.get('byextent')
    if byextent:
        q = _filter_by_extent(MapIndex, q, byextent)
        
    byadded = parse_by_added(kw.get('byadded'))
    if byadded:
        q = q.filter(last_modified__gte=byadded)
    
    byperiod = kw.get('byperiod')
    if byperiod:
        q = _filter_by_period(MapIndex, q, byperiod)
        
    if not settings.USE_GEONETWORK:
        bykw = kw.get('bykw')
        if bykw:
            # this is a somewhat nested query but it performs way faster
            layers_with_kw = Layer.objects.filter(_build_kw_only_query(bykw)).values('typename')
            map_layers_with = MapLayer.objects.filter(name__in=layers_with_kw).values('map')
            q = q.filter(id__in=map_layers_with)
        if query:
            rules = _rank_rules(Map,
                ['title',10, 5],
                ['abstract',5, 2],
            )
            q = _add_relevance(q, query, rules)
    
    results.extend( _process_results( map(MapNormalizer,q) ))
    
    
def _add_relevance(query, text, rank_rules):
    eq = """CASE WHEN %s = '%s' THEN %s ELSE 0 END"""
    frag = """CASE WHEN position(lower('%s') in lower(%s)) >= 1 THEN %s ELSE 0 END"""
    
    preds = []

    preds.extend( [ eq % (r[0],text,r[1]) for r in rank_rules] )
    preds.extend( [ frag % (text,r[0],r[2]) for r in rank_rules] )
    
    words = _split_query(text)
    if len(words) > 1:
        for w in words:
            preds.extend( [ frag % (w,r[0],r[2] / 2) for r in rank_rules] )
            
    sql = " + ".join(preds)
            
    # ugh - work around bug
    query = query.defer(None)
    return query.extra(select={'relevance':sql})
    
def _build_kw_query(query, query_keywords=False):
    '''Build an OR query on title and abstract from provided search text.
    if query_keywords is provided, include a query on the keywords attribute
    return a Q object
    '''
    kws = _split_query(query)
    subquery = [
        Q(title__icontains=kw) | Q(abstract__icontains=kw) for kw in kws
    ]
    if query_keywords:
        subquery = [ q | Q(keywords__name__icontains=kw) for q in subquery ]
    return reduce( operator.or_, subquery)

def _build_kw_only_query(query):
    return reduce(operator.or_, [Q(keywords__name__contains=kw) for kw in _split_query(query)])

def _filter_by_extent(index, q, byextent, user=False):
    env = Envelope(map(float,byextent.split(',')))
    extent_ids = index.objects.filter(extent__contained=env.wkt)
    if user:
        extent_ids = extent_ids.values('indexed__owner')
        return q.filter(user__in=extent_ids)
    else:
        extent_ids = extent_ids.values('indexed')
        return q.filter(id__in=extent_ids)
    
def _filter_by_period(index, q, byperiod, user=False):
    period_ids = filter_by_period(index, byperiod[0], byperiod[1])
    if user:
        period_ids = period_ids.values('indexed__owner')
        return q.filter(user__in=period_ids)
    else:
        period_ids = period_ids.values('indexed')
        return q.filter(id__in=period_ids)
    
def parse_by_added(spec):
    td = None
    if spec == 'today':
        td = timedelta(days=1)
    elif spec == 'week':
        td = timedelta(days=7)
    elif spec == 'month':
        td = timedelta(days=30)
    else:
        return None
    return date.today() - td
        
def _get_layer_results(results, query, kw):
    
    layer_results = None
    
    if settings.USE_GEONETWORK:
        # cache geonetwork results
        cache_key = query and 'search_results_%s' % query or 'search_results'
        layer_results = cache.get(cache_key)
        if not layer_results:
            layer_results = _metadata_search(query, 0, 1000)['rows']
            layer_results = filter(_filter_results, layer_results)
            # @todo search cache timeout in settings?
            cache.set(cache_key, layer_results, timeout=300)
        q = Layer.objects.filter(uuid__in=[ doc['uuid'] for doc in layer_results ])
    else:
        q = _layer_query(query,kw)
        if _exclude_patterns:
            name_filter = reduce(operator.or_,[ Q(name__regex=f) for f in _exclude_patterns])
            q = q.exclude(name_filter)
        if query:
            q = q.filter(_build_kw_query(query,True)) | q.filter(name__icontains = query)
        # we can optimize kw search here
        # maps will still be slow, but this way all the layers are filtered
        # bybw before the cruddy in-memory filter
        bykw = kw.get('bykw')
        if bykw:
            q = q.filter(_build_kw_only_query(bykw))
            
    byowner = kw.get('byowner')
    if byowner:
        q = q.filter(owner__username=byowner)
            
    bytype = kw.get('bytype')
    if bytype and bytype != 'layer':
        q = q.filter(storeType = bytype)
        
    byextent = kw.get('byextent')
    if byextent:
        q = _filter_by_extent(LayerIndex, q, byextent)
        
    byadded = parse_by_added(kw.get('byadded'))
    if byadded:
        q = q.filter(date__gte=byadded)
        
    byperiod = kw.get('byperiod')
    if byperiod:
        q = _filter_by_period(LayerIndex, q, byperiod)
       
    # this is a special optimization for prefetching results when requesting
    # all records via search
    # keywords and thumbnails cannot be prefetched at the moment due to
    # the way the contenttypes are implemented
    if kw['limit'] == 0:
        q = q.defer(None).prefetch_related("owner","spatial_temporal_index")
    
    # if we're using geonetwork, have to fetch the results from that
    if layer_results:
        normalizers = []
        layers = dict([ (l.uuid,l) for l in q])
    
        for doc in layer_results:
            layer = layers.get(doc['uuid'],None)
            if layer is None: continue #@todo - remote layer (how to get last_modified?)
            normalizers.append(LayerNormalizer(layer,doc))
    else:
        if query:
            rules = _rank_rules(Layer,
                ['name',10, 1],
                ['title',10, 5],
                ['abstract',5, 2],
            )
            q = _add_relevance(q, query, rules)
        normalizers = map(LayerNormalizer, q)
    _process_results(normalizers)
    results.extend(normalizers)
                

def combined_search_results(query, kw):
    results = []
    
    bytype = kw.get('bytype', None)
    
    if bytype is None or bytype == u'map':
        _get_map_results(results, query, kw)
        
    if bytype is None or bytype == u'layer':
        _get_layer_results(results, query, kw)
        
    if bytype is None or bytype == u'owner':
        _get_owner_results(results, query, kw)
        
    return results