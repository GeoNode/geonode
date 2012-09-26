from geonode.utils import _split_query

from datetime import date
from datetime import timedelta
import operator

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10

_SEARCH_PARAMS = [
    'type',
    'kw',
    'owner',
    'extent',
    'added',
    'period',
    'start',
    'end',
    'exclude',
    'cache']


class Query(object):
    # search params
    query = None
    'search terms, query, keyword(s)'

    split_query = None
    'the query, but split into pieces'
    
    period = None
    extent = None
    
    params = None
    'dict of specific field queries, use the fields for easier access'
    
    # sorting
    sort = None
    'relevance, alpha, rating, created, updated'
    
    order = None
    
    # other
    user = None
    cache = True
    
    # paging
    start = None
    limit = None
    
    def __init__(self, query, start=0, limit=DEFAULT_MAPS_SEARCH_BATCH_SIZE, 
                 sort_field='last_modified', sort_asc=False, filters=None,
                 user=None, cache=True, **kwargs):
        self.query = query
        self.split_query = _split_query(query)
        self.start = start
        self.limit = limit
        self.sort = sort_field
        self.order = sort_asc
        self.params = filters or {}
        self.user = user
        
        self.type = filters.get('type')
        self.owner = filters.get('owner')
        self.kw = filters.get('kw')
        
        val = filters['period']
        self.period = tuple(val.split(',')) if val else None
            
        val = filters['extent']
        self.extent = map(float, filters.get('extent').split(',')) if val else None
        
        val = filters['added']
        self.added = parse_by_added(val) if val else None


    def cache_key(self):
        fhash = reduce(operator.xor, map(hash, self.params.items()))
        return str(fhash ^ hash(self.user) ^ hash(self.query))


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


def query_from_request(**params):
    
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
    
    # compat
    aliases = dict(type='bytype',bbox='byextent')
    for k,v in aliases.items():
        if k in params: filters[v] = params[k]
                
    cache = params.get('cache',True)
    
    return Query(**locals())
    
    