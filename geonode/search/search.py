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

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import backend
from django.db.models import Q

from geonode.security.models import UserObjectRoleMapping, GenericObjectRoleMapping
from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.people.models import Profile
from geonode.base.models import TopicCategory, ResourceBase

from geonode.search import extension
from geonode.search.models import filter_by_period
from geonode.search.models import filter_by_extent
from geonode.search.models import using_geodjango

import operator


def _rank_rules(model, *rules):
    # prefix field names with model's db table to avoid ambiguity
    return [('"%s"."%s"' % (model._meta.db_table, r[0]), r[1], r[2])
            for r in rules]


def _filter_results(l):
    '''If the layer name doesn't match any of the patterns, it shows in the results'''
    return not any(p.search(l['name']) for p in extension.exclude_regex)


def _filter_security(q, user, model, permission):
    '''apply filters to the query that remove those model objects that are
    not viewable by the given user based on row-level permissions'''
    # superusers see everything
    if user and user.is_superuser: return q

    # resolve the model permission
    ct = ContentType.objects.get_for_model(model)
    p = Permission.objects.get(content_type=ct, codename=permission)

    # apply generic role filters
    generic_roles = [ANONYMOUS_USERS]
    if user and not user.is_anonymous():
        generic_roles.append(AUTHENTICATED_USERS)
    grm = GenericObjectRoleMapping.objects.filter(object_ct=ct, role__permissions__in=[p], subject__in=generic_roles).values('object_id')
    q = q.filter(id__in=grm)

    # apply specific user filters
    if user and not user.is_anonymous():
        urm = UserObjectRoleMapping.objects.filter(object_ct=ct, role__permissions__in=[p], user=user).values('object_id')
        q = q | q.filter(id__in=urm)
        # if the user is the owner, make sure these are included
        q = q | getattr(model, 'objects').filter(owner=user)

    return q

def _filter_category(q, categories):
    _categories = []
    for category in categories:
        try:
            _categories.append(TopicCategory.objects.get(slug=category))
        except TopicCategory.DoesNotExist:
            # FIXME Do something here
            pass

    return q.filter(category__in=_categories)

def _add_relevance(query, rank_rules):
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
    return sql


def _safely_add_relevance(q, query, rank_rules):
    # for unittests, it doesn't make sense to test this as it's postgres
    # specific SQL - instead test/verify directly using a query and getting SQL
    if 'sqlite' in backend.__name__: return q

    sql = _add_relevance(query, rank_rules)
    # ugh - work around bug
    q = q.defer(None)
    return q.extra(select={'relevance':sql})


def _build_map_layer_text_query(q, query, query_keywords=False):
    '''Build an OR query on title and abstract from provided search text.
    if query_keywords is provided, include a query on the keywords attribute if
    specified.

    return a Q object
    '''
    # title or abstract contains entire phrase
    subquery = [Q(title__icontains=query.query),Q(abstract__icontains=query.query)]
    # tile or abstract contains pieces of entire phrase
    if len(query.split_query) > 1:
        subquery.extend([Q(title__icontains=kw) for kw in query.split_query])
        subquery.extend([Q(abstract__icontains=kw) for kw in query.split_query])
    # or keywords match any pieces of entire phrase
    if query_keywords and query.split_query:
        subquery.append(_build_kw_only_query(query.split_query))
    # if any OR phrases exists, build them
    if subquery:
        q = q.filter(reduce( operator.or_, subquery))
    return q


def _build_kw_only_query(keywords):
    return reduce(operator.or_, [Q(keywords__name__contains=kw) for kw in keywords])

def _get_owner_results(query):
    # make sure all contacts have a user attached
    q = extension.owner_query(query)

    if q is None: return None

    if query.kw:
        # hard to handle - not supporting at the moment
        return Profile.objects.none()

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
                _rank_rules(Profile,['organization', 5, 2])
        added = extension.owner_rank_rules()
        if added:
            rules = rules + _rank_rules(*added)
        q = _safely_add_relevance(q, query, rules)

    return q.distinct()


def _get_map_results(query):
    q = extension.map_query(query)

    q = _filter_security(q, query.user, Map, 'view_map')

    if query.owner:
        q = q.filter(owner__username=query.owner)

    if query.extent:
        q = filter_by_extent(Map, q, query.extent)

    if query.added:
        q = q.filter(last_modified__gte=query.added)

    if query.period:
        q = filter_by_period(Map, q, *query.period)

    if query.kw:
        q = q.filter(_build_kw_only_query(query.kw))

    if query.exclude:
        q = q.exclude(reduce(operator.or_, [Q(title__contains=ex) for ex in query.exclude]))

    if query.categories:
        q = _filter_category(q, query.categories)

    if query.query:
        q = _build_map_layer_text_query(q, query, query_keywords=True)
        rules = _rank_rules(ResourceBase,
            ['title',10, 5],
            ['abstract',5, 2],
        )
        q = _safely_add_relevance(q, query, rules)

    return q.distinct()


def _get_layer_results(query):

    q = extension.layer_query(query)

    q = _filter_security(q, query.user, Layer, 'view_layer')

    if extension.exclude_patterns:
        name_filter = reduce(operator.or_,[ Q(name__regex=f) for f in extension.exclude_patterns])
        q = q.exclude(name_filter)

    if query.kw:
        q = q.filter(_build_kw_only_query(query.kw))

    if query.exclude:
        q = q.exclude(reduce(operator.or_, [Q(title__contains=ex) for ex in query.exclude]))

    if query.owner:
        q = q.filter(owner__username=query.owner)

    if query.extent:
        q = filter_by_extent(Layer, q, query.extent)

    if query.added:
        q = q.filter(date__gte=query.added)

    if query.period:
        q = filter_by_period(Layer, q, *query.period)

    if query.categories:
        q = _filter_category(q, query.categories)

    # this is a special optimization for prefetching results when requesting
    # all records via search
    # keywords and thumbnails cannot be prefetched at the moment due to
    # the way the contenttypes are implemented
    if query.limit == 0 and using_geodjango:
        q = q.defer(None).prefetch_related("owner","spatial_temporal_index")

    if query.query:
        q = _build_map_layer_text_query(q, query, query_keywords=True) |\
            q.filter(name__icontains=query.query) # map doesn't have name
        rules = _rank_rules(ResourceBase,
            ['title',10, 5],
            ['abstract',5, 2],
        )
        q = _safely_add_relevance(q, query, rules)

    return q.distinct()

def _get_document_results(query):

    q = extension.document_query(query)

    q = _filter_security(q, query.user, Document, 'view_document')

    if extension.exclude_patterns:
        name_filter = reduce(operator.or_,[ Q(name__regex=f) for f in extension.exclude_patterns])
        q = q.exclude(name_filter)

    if query.kw:
        q = q.filter(_build_kw_only_query(query.kw))

    if query.exclude:
        q = q.exclude(reduce(operator.or_, [Q(title__contains=ex) for ex in query.exclude]))

    if query.owner:
        q = q.filter(owner__username=query.owner)

    if query.extent:
        q = filter_by_extent(Document, q, query.extent)

    if query.added:
        q = q.filter(date__gte=query.added)

    if query.period:
        q = filter_by_period(Document, q, *query.period)

    if query.categories:
        q = _filter_category(q, query.categories)

    # this is a special optimization for prefetching results when requesting
    # all records via search
    # keywords and thumbnails cannot be prefetched at the moment due to
    # the way the contenttypes are implemented
    if query.limit == 0 and using_geodjango:
        q = q.defer(None).prefetch_related("owner","spatial_temporal_index")

    if query.query:
        q = _build_map_layer_text_query(q, query, query_keywords=True)
        rules = _rank_rules(ResourceBase,
            ['title',10, 5],
            ['abstract',5, 2],
        )
        q = _safely_add_relevance(q, query, rules)

    return q.distinct()

def combined_search_results(query):
    facets = dict([ (k,0) for k in ('map', 'layer', 'vector', 'raster', 'document', 'user')])
    results = {'facets' : facets}

    bytype = (None,) if u'all' in query.type else query.type
    query.type = bytype

    if None in bytype  or u'map' in bytype:
        q = _get_map_results(query)
        facets['map'] = q.count()
        results['maps'] = q

    if None in bytype or u'layer' in bytype or u'raster' in bytype or u'vector' in bytype:
        q = _get_layer_results(query)
        if u'raster' in bytype and not u'vector' in bytype:
            q = q.filter(storeType='coverageStore')
        if u'vector' in bytype and not u'raster' in bytype:
            q = q.filter(storeType='dataStore')
        facets['layer'] = q.count()
        facets['raster'] = q.filter(storeType='coverageStore').count()
        facets['vector'] = q.filter(storeType='dataStore').count()
        results['layers'] = q

    if None in bytype or u'document' in bytype:
        q = _get_document_results(query)
        facets['document'] = q.count()
        results['documents'] = q

    if query.categories and len(query.categories) == TopicCategory.objects.count() or not query.categories:
        if None in bytype or u'user' in bytype:
            q = _get_owner_results(query)
            facets['user'] = q.count()
            results['users'] = q
    
    return results
