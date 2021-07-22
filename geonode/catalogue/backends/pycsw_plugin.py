#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import logging

from django.db import connection
from django.db.models import Max, Min, Count
from django.conf import settings

from pycsw.core.repository import Repository, query_spatial, get_geometry_area

from geonode.base.models import ResourceBase

from pycsw.core import util

LOGGER = logging.getLogger(__name__)

GEONODE_SERVICE_TYPES = {
    # 'GeoNode enum': 'CSW enum'
    'http://www.opengis.net/cat/csw/2.0.2': 'OGC:CSW',
    'http://www.opengis.net/wms': 'OGC:WMS',
    'http://www.opengis.net/wmts/1.0': 'OGC:WMTS',
    'https://wiki.osgeo.org/wiki/TMS': 'OSGeo:TMS',
    'urn:x-esri:serviceType:ArcGIS:MapServer': 'ESRI:ArcGIS:MapServer',
    'urn:x-esri:serviceType:ArcGIS:ImageServer': 'ESRI:ArcGIS:ImageServer'
}


class GeoNodeRepository(Repository):
    """
    Class to interact with underlying repository
    """

    def __init__(self, context, repo_filter=None):
        """
        Initialize repository
        """

        self.context = context
        self.filter = repo_filter
        self.fts = False
        self.label = 'GeoNode'
        self.local_ingest = True

        self.dbtype = settings.DATABASES['default']['ENGINE'].split('.')[-1]

        # GeoNode PostgreSQL installs are PostGIS enabled
        if self.dbtype == 'postgis':
            self.dbtype = 'postgresql+postgis+wkt'

        if self.dbtype in {'sqlite', 'sqlite3'}:  # load SQLite query bindings
            connection.connection.create_function(
                'query_spatial', 4, query_spatial)
            connection.connection.create_function(
                'get_anytext', 1, util.get_anytext)
            connection.connection.create_function(
                'get_geometry_area', 1, get_geometry_area)

        # generate core queryables db and obj bindings
        self.queryables = {}

        for tname in self.context.model['typenames']:
            for qname in self.context.model['typenames'][tname]['queryables']:
                self.queryables[qname] = {}
                items = list(self.context.model['typenames'][tname]['queryables'][qname].items())

                for qkey, qvalue in items:
                    self.queryables[qname][qkey] = qvalue

        # flatten all queryables
        # TODO smarter way of doing this
        self.queryables['_all'] = {}
        for qbl in self.queryables:
            self.queryables['_all'].update(self.queryables[qbl])
        self.queryables['_all'].update(self.context.md_core_model['mappings'])

        if 'Harvest' in self.context.model['operations'] and 'Transaction' in self.context.model['operations']:
            self.context.model['operations']['Harvest']['parameters']['ResourceType']['values'] = list(GEONODE_SERVICE_TYPES.keys())  # noqa
            self.context.model['operations']['Transaction']['parameters']['TransactionSchemas']['values'] = list(GEONODE_SERVICE_TYPES.keys())  # noqa

    def dataset(self):
        """
        Stub to mock a pycsw dataset object for Transactions
        """
        return type('ResourceBase', (object,), {})

    def query_ids(self, ids):
        """
        Query by list of identifiers
        """

        results = self\
            ._get_repo_filter(ResourceBase.objects)\
            .filter(uuid__in=ids)\
            .all()

        return results

    def query_domain(self, domain, typenames,
                     domainquerytype='list', count=False):
        """
        Query by property domain values
        """

        objects = self._get_repo_filter(ResourceBase.objects)

        if domainquerytype == 'range':
            return [tuple(objects.aggregate(
                Min(domain), Max(domain)).values())]
        else:
            if count:
                return [(d[domain], d[f'{domain}__count'])
                        for d in objects.values(domain).annotate(Count(domain))]
            else:
                return objects.values_list(domain).distinct()

    def query_insert(self, direction='max'):
        """
        Query to get latest (default) or earliest update to repository
        """
        if direction == 'min':
            return ResourceBase.objects.aggregate(
                Min('last_updated'))['last_updated__min'].strftime('%Y-%m-%dT%H:%M:%SZ')
        return self._get_repo_filter(ResourceBase.objects).aggregate(
            Max('last_updated'))['last_updated__max'].strftime('%Y-%m-%dT%H:%M:%SZ')

    def query_source(self, source):
        """
        Query by source
        """
        return self._get_repo_filter(ResourceBase.objects).filter(url=source)

    def query(self, constraint, sortby=None, typenames=None,
              maxrecords=10, startposition=0):
        """
        Query records from underlying repository
        """

        # run the raw query and get total
        # we want to exclude layers which are not valid, as it is done in the
        # search engine
        pycsw_filters = settings.PYCSW.get('FILTER', {'resource_type__in': ['dataset']})

        if 'where' in constraint:  # GetRecords with constraint
            query = self._get_repo_filter(
                ResourceBase.objects.filter(**pycsw_filters)).extra(
                where=[
                    constraint['where']],
                params=constraint['values'])
        else:  # GetRecords sans constraint
            query = self._get_repo_filter(
                ResourceBase.objects.filter(**pycsw_filters))

        total = query.count()

        # apply sorting, limit and offset
        if sortby is not None:
            if 'spatial' in sortby and sortby['spatial']:  # spatial sort
                desc = False
                if sortby['order'] == 'DESC':
                    desc = True
                query = query.all()
                return [str(total),
                        sorted(query,
                               key=lambda x: float(util.get_geometry_area(
                                   getattr(x, sortby['propertyname']))),
                               reverse=desc,
                               )[startposition:startposition + int(maxrecords)]]
            else:
                if sortby['order'] == 'DESC':
                    pname = f"-{sortby['propertyname']}"
                else:
                    pname = sortby['propertyname']
                return [str(total),
                        query.order_by(pname)[startposition:startposition + int(maxrecords)]]
        else:  # no sort
            return [str(total), query.all()[
                startposition:startposition + int(maxrecords)]]

    def delete(self, constraint):
        """
        Delete a record from the repository
        """

        results = self._get_repo_filter(ResourceBase.objects).extra(where=[constraint['where']],
                                                                    params=constraint['values']).all()
        deleted = len(results)
        results.delete()
        return deleted

    def _get_repo_filter(self, query):
        """
        Apply repository wide side filter / mask query
        """
        if self.filter is not None:
            return query.extra(where=[self.filter])
        return query
