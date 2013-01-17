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

from geonode.layers.models import Layer, ResourceBase
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.layers.models import add_bbox_query
from geonode.search.util import iso_fmt

from datetime import datetime

def filter_by_period(model, q, start, end, user=None):
    '''modify the query to filter the given model for dates between start and end
    start, end - iso str ('-5000-01-01T12:00:00Z')
    '''

    parse = lambda v: datetime.strptime(v, iso_fmt)  
    if issubclass(model, ResourceBase) and not user:
        if start:
            q = q.filter(date__gte = parse(start))
        if end:    
            q = q.filter(date__lte = parse(end))
    else:
        # @todo handle map and/or users - either directly if implemented or ...
        # this will effectively short-circuit the query at this point
        q = q.none()
    return q

def filter_by_extent(model, q, extent, user=None):
    '''modify the query to filter the given model for the provided extent and optional user
    extent: tuple of float coordinates representing x0,x1,y0,y1
    '''
    if issubclass(model, ResourceBase) and not user:
        q = add_bbox_query(q, extent)
    else:
        # @todo handle map and/or users - either directly if implemented or ...
        # this will effectively short-circuit the query at this point
        q = q.none()
    return q

using_geodjango = False

if 'django.contrib.gis' in settings.INSTALLED_APPS:
    from geonode.search.geomodels import *
    using_geodjango = True
