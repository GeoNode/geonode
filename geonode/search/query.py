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

from geonode.search.util import resolve_extension
from geonode.utils import _split_query

from django.conf import settings

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

# settings API
_search_config = getattr(settings,'SIMPLE_SEARCH_SETTINGS', {})
_SEARCH_PARAMS.extend(_search_config.get('extra_query',[]))
_extra_context = resolve_extension('extra_context')
# end settings API


class BadQuery(Exception):
    pass


class Query(object):
    # while these are all class attributes, they will be overwritten

    # search params
    query = None
    'search terms, query, keyword(s)'

    split_query = None
    'the query, but split into pieces'

    period = None
    'tuple of start/end date'
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
                 user=None, cache=True):
        self.query = query
        self.split_query = _split_query(query)
        self.start = start
        self.limit = limit
        self.sort = sort_field
        self.order = sort_asc
        self.params = filters or {}
        self.user = user
        self.cache = cache

        self.type = filters.get('type')
        self.owner = filters.get('owner')
        self.kw = filters.get('kw')
        if self.kw:
            self.kw = tuple(self.kw.split(','))

        val = filters['period']
        self.period = tuple(val.split(',')) if val else None

        start = filters['start']
        end = filters['end']
        if start or end:
            if self.period:
                raise BadQuery('period and start/end both provided')
            self.period = (start, end)

        val = filters['extent']
        if val:
            try:
                err = BadQuery('extent filter must contain x0,x1,y0,y1 comma separated')
                parts = val.split(',')
                if len(parts) != 4:
                    raise err
                self.extent = map(float, parts)
            except:
                raise err

        val = filters['added']
        self.added = parse_by_added(val) if val else None


    def cache_key(self):
        '''the cache key is based on filters, the user and the text query'''
        fhash = reduce(operator.xor, map(hash, self.params.items()))
        return str(fhash ^ hash(self.user.username if self.user else 31) ^ hash(self.query))


    def get_query_response(self):
        '''return a dict containing any non-null parameters used in the search'''
        q = dict([ kv for kv in self.params.items() if kv[1] ])
        if self.query:
            q['query'] = self.query
        return q


def parse_by_added(spec):
    if spec == 'today':
        td = timedelta(days=1)
    elif spec == 'week':
        td = timedelta(days=7)
    elif spec == 'month':
        td = timedelta(days=30)
    else:
        raise BadQuery('valid added filter values are: today,week,month')
    return date.today() - td


def query_from_request(request, extra):
    params = dict(request.REQUEST)
    params.update(extra)

    query = params.get('q', '')
    try:
        start = int(params.get('startIndex', 0))
    except ValueError:
        raise BadQuery('startIndex must be valid number')
    try:
        limit = int(params.get('limit', DEFAULT_MAPS_SEARCH_BATCH_SIZE))
    except ValueError:
        raise BadQuery('limit must be valid number')

    # handle old search link parameters
    if 'sort' in params and 'dir' in params:
        sort_field = params['sort']
        sort_asc = params['dir'] == 'ASC'
    else:
        sorts = {
            'newest' : ('last_modified',False),
            'oldest' : ('last_modified',True),
            'alphaaz' : ('title',True),
            'alphaza' : ('title',False),
            'popularity' : ('rank',False),
            'rel' : ('relevance',False)
        }
        try:
            sort_field, sort_asc = sorts[params.get('sort','newest')]
        except KeyError:
            raise BadQuery('valid sorting values are: %s' % sorts.keys())

    filters = dict([(k,params.get(k,None) or None) for k in _SEARCH_PARAMS])

    aliases = dict(bbox='extent')
    for k,v in aliases.items():
        if k in params: filters[v] = params[k]

    cache = bool(params.get('cache', True))
    return Query(query, start=start, limit=limit, sort_field=sort_field,
                 sort_asc=sort_asc, filters=filters, cache=cache, user=request.user)


